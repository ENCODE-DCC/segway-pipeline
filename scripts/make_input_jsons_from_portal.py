import argparse
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import urljoin

import httpx

InputJson = Dict[str, Union[float, int, str, List[str]]]

PORTAL_URL = "https://www.encodeproject.org/"
WORKFLOW_NAME = "segway"
EXCLUDED_STATUSES = ("revoked", "archived", "replaced", "deleted")
DATASET_OUTPUT_TYPE = {
    "ATAC-seq": "fold change_over control",
    "DNase-seq": "read-depth normalized signal",
    "Histone ChIP-seq": "fold change over control",
    "TF ChIP-seq": "fold change over control",
}


class UrlJoiner:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self.base_is_valid = False

    @staticmethod
    def validate_base_url(base_url):
        if not base_url.endswith("/"):
            raise ValueError("Base url must end with a `/`")
        return base_url

    @property
    def base_url(self):
        if not self.base_is_valid:
            self._base_url = self.validate_base_url(self._base_url)
            self.base_is_valid = True
        return self._base_url

    def resolve(self, path: str):
        return urljoin(self.base_url, path)


def main():
    parser = get_parser()
    args = parser.parse_args()
    keypair = get_keypair(args.keypair)
    urljoiner = UrlJoiner(PORTAL_URL)
    epigenome_id = (
        "/".join(("reference-epigenomes", args.accession))
        if not args.accession.startswith("reference-epigenomes")
        else args.accession
    )
    reference_epigenome_url, chrom_sizes_url, annotation_url = map(
        urljoiner.resolve, (epigenome_id, args.chrom_sizes, args.annotation_gtf)
    )
    reference_epigenome = get_json(reference_epigenome_url, auth=keypair)
    assembly = get_assembly(chrom_sizes_url)
    portal_files = get_portal_files(reference_epigenome, assembly, urljoiner)
    extra_props = get_extra_props_from_args(args, chrom_sizes_url, annotation_url)
    input_json = make_input_json(portal_files, extra_props)
    outfile = args.outfile if args.outfile is not None else f"{args.accession}.json"
    write_json(input_json, outfile)


def get_keypair(keypair_path: Optional[str]) -> Optional[Tuple[str, str]]:
    if keypair_path is None:
        return None
    with open(keypair_path) as f:
        data = json.load(f)
    try:
        submit = data["submit"]
        key = submit["key"]
        secret = submit["secret"]
    except KeyError as e:
        raise KeyError(
            'Invalid keypairs file, must take the form of {"submit": {"key": ... , "secret": ...}}'
        ) from e
    return key, secret


def get_portal_files(
    reference_epigenome: Dict[str, Any], assembly: str, urljoiner: UrlJoiner
) -> List[str]:
    datasets_files: Dict[str, str] = {}
    for dataset in reference_epigenome["related_datasets"]:
        assay_title = dataset["assay_title"]
        at_id = dataset["@id"]
        if assay_title not in DATASET_OUTPUT_TYPE.keys():
            continue
        bioreps = set(
            i["biological_replicate_number"]
            for i in filter_by_status(dataset["replicates"])
        )
        num_bioreps = len(bioreps)
        files = filter_by_status(dataset["files"])
        is_replicated_dnase = assay_title == "DNase-seq" and num_bioreps > 1
        if is_replicated_dnase:
            preferred_replicate = get_dnase_preferred_replicate(files, urljoiner)
        for file in files:
            if file["file_format"] != "bigWig" or file["assembly"] != assembly:
                continue
            if is_replicated_dnase:
                if sorted(file["biological_replicates"]) != sorted(preferred_replicate):
                    continue
            elif len(file["biological_replicates"]) < num_bioreps:
                continue
            if file["output_type"] == DATASET_OUTPUT_TYPE[assay_title]:
                if at_id not in datasets_files:
                    datasets_files[at_id] = get_url_from_file_obj(file)
                else:
                    raise ValueError(
                        (
                            f"Found more than one file for dataset {at_id}: found "
                            f"{file['@id']} but already found "
                            f"{datasets_files[at_id]}"
                        )
                    )
    return list(datasets_files.values())


def get_extra_props_from_args(
    args: argparse.Namespace, chrom_sizes_url: str, annotation_url: str
) -> InputJson:
    extra_props = {k: v for k, v in vars(args).items() if v is not None}
    extra_props.pop("accession")
    extra_props.pop("outfile", None)
    extra_props.pop("keypair", None)
    extra_props["chrom_sizes"] = get_url_for_file(chrom_sizes_url)
    extra_props["annotation_gtf"] = get_url_for_file(annotation_url)
    return extra_props


def get_assembly(chrom_sizes_url: str) -> str:
    file = get_json(chrom_sizes_url)
    try:
        assembly = file["assembly"]
    except KeyError as e:
        raise ValueError("Chrom sizes file does not have an assembly") from e
    return assembly


def make_input_json(portal_files: List[str], extra_props: InputJson) -> InputJson:
    input_json: InputJson = {}
    input_json[f"{WORKFLOW_NAME}.bigwigs"] = portal_files
    input_json.update({f"{WORKFLOW_NAME}.{k}": v for k, v in extra_props.items()})
    return input_json


def get_json(url: str, auth: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
    """
    A wrapper around httpx get potentially with an auth keypair that always asks for
    JSON.
    """
    response = httpx.get(url, auth=auth, headers={"Accept": "application/json"})
    response.raise_for_status()
    res = response.json()
    if not isinstance(res, dict):
        raise TypeError(f"Got a JSON array from url {url}, expected object")
    return res


def get_url_from_file_obj(portal_file: Dict[str, Any]) -> str:
    try:
        url = portal_file["cloud_metadata"]["url"]
    except KeyError as e:
        raise KeyError(
            f"Could not identify cloud metadata from portal file {portal_file['@id']}"
        ) from e
    return url


def get_url_for_file(file_url: str) -> str:
    file_obj = get_json(file_url)
    file_s3_url = get_url_from_file_obj(file_obj)
    return file_s3_url


def filter_by_status(objs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered = []
    for obj in objs:
        if obj["status"] not in EXCLUDED_STATUSES:
            filtered.append(obj)
    return filtered


def get_dnase_preferred_replicate(
    files: List[Dict[str, Any]], urljoiner: UrlJoiner
) -> List[int]:
    bams = [i for i in files if i["output_type"] == "alignments"]
    max_mapped_read_count = -1
    for bam in bams:
        samtools_flagstats = [
            i for i in bam["quality_metrics"] if i.startswith("/samtools-flagstats")
        ]
        if len(samtools_flagstats) != 1:
            raise ValueError(
                f"Expected one samtools flagstats quality metric for file {bam['@id']}, found {len(samtools_flagstats)}"
            )
        qc = get_json(urljoiner.resolve(samtools_flagstats[0]))
        qc_mapped_read_count = qc["mapped"]
        if qc_mapped_read_count > max_mapped_read_count:
            preferred_replicate = bam["biological_replicates"]
            max_mapped_read_count = qc_mapped_read_count
    return preferred_replicate


def write_json(input_json: InputJson, path: str):
    with open(path, "w") as f:
        f.write(json.dumps(input_json, indent=4))


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--accession",
        required=True,
        help="Accession of reference epigenome on the ENCODE portal",
    )
    parser.add_argument(
        "-n",
        "--num-segway-cpus",
        type=int,
        help="Number of cpus to use for Segway training and annotation, if not specified will use pipeline defaults",
    )
    parser.add_argument(
        "-f",
        "--minibatch-fraction",
        type=float,
        help="Fraction of genome to sample for each round of training, if not specified will use pipeline defaults",
    )
    parser.add_argument(
        "-r",
        "--max-train-rounds",
        type=int,
        help="Maximum number of rounds for Segway training, if not specified will use pipeline defaults",
    )
    parser.add_argument(
        "-i",
        "--num-instances",
        type=int,
        help="Number of Segway models to train in parallel, if not specified will use pipeline defaults",
    )
    parser.add_argument(
        "-p",
        "--prior-strength",
        type=float,
        help="Coefficient for segment length prior, if not specified will use pipeline defaults",
    )
    parser.add_argument(
        "-s",
        "--segtransition-weight-scale",
        type=float,
        help="Coefficient for segment length prior, if not specified will use pipeline defaults",
    )
    parser.add_argument(
        "-g",
        "--annotation-gtf",
        required=True,
        help=(
            "ENCODE ID corresponding to the GENCODE annotation GTF to use as input for "
            "the pipeline, e.g. `gencode.v29.primary_assembly.annotation_UCSC_names`"
        ),
    )
    parser.add_argument(
        "-c",
        "--chrom-sizes",
        required=True,
        help=(
            "ENCODE ID corresponding to the chrom sizes file to use as input to the "
            "pipeline, e.g. `GRCh38_EBV.chrom.sizes`"
        ),
    )
    parser.add_argument("-o", "--outfile", help="Name of file to output the input JSON")
    parser.add_argument(
        "-k",
        "--keypair",
        help="Path to JSON file containing portal API keys, only needed for in progress data",
    )
    return parser


if __name__ == "__main__":
    main()
