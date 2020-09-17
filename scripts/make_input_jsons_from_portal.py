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
    "ATAC-seq": "fold change over control",
    "DNase-seq": "read-depth normalized signal",
    "Histone ChIP-seq": "fold change over control",
    "TF ChIP-seq": "fold change over control",
}


class UrlJoiner:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self.base_is_valid = False

    @staticmethod
    def validate_base_url(base_url: str) -> str:
        if not base_url.endswith("/"):
            raise ValueError("Base url must end with a `/`")
        return base_url

    @property
    def base_url(self) -> str:
        if not self.base_is_valid:
            self._base_url = self.validate_base_url(self._base_url)
            self.base_is_valid = True
        return self._base_url

    def resolve(self, path: str) -> str:
        """
        Resolves paths like foo/bar to base.url/foo/bar
        """
        if path.startswith(self.base_url):
            return path
        return urljoin(self.base_url, path)


class Client:
    def __init__(self, base_url: str = PORTAL_URL, keypair_path: Optional[str] = None):
        self.url_joiner = UrlJoiner(base_url)
        self._keypair_path = keypair_path
        self._keypairs: Optional[Tuple[str, str]] = None

    @property
    def keypair(self) -> Optional[Tuple[str, str]]:
        if self._keypairs is None:
            self._keypairs = self._get_keypair()
        return self._keypairs

    def _get_keypair(self) -> Optional[Tuple[str, str]]:
        if self._keypair_path is None:
            return None
        with open(self._keypair_path) as f:
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

    def get_json(self, url_or_path: str) -> Dict[str, Any]:
        """
        A wrapper around httpx get potentially with an auth keypair that always asks for
        JSON.
        """
        url = self.url_joiner.resolve(url_or_path)
        response = httpx.get(
            url, auth=self.keypair, headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        res = response.json()
        if not isinstance(res, dict):
            raise TypeError(f"Got a JSON array from url {url}, expected object")
        return res

    def get_reference_epigenome(self, url_or_path: str) -> Dict[str, Any]:
        """
        Original files are not embedded in the datasets, need to embed them manually.
        Batch them using a query to save on individual requests.
        """
        reference_epigenome = self.get_json(url_or_path)
        for dataset in reference_epigenome["related_datasets"]:
            query_params = [("type", "File")]
            query_params.extend(("@id", f) for f in dataset["original_files"])
            query_params.append(("frame", "object"))
            original_files = self.search(query_params)
            dataset["original_files"] = original_files
        return reference_epigenome

    def search(self, query_params: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        path = self._make_query_path(query_params)
        result = self.get_json(path)
        return result["@graph"]

    def _make_query_path(self, query_params: List[Tuple[str, str]]) -> str:
        """
        Generate the query string for the ENCODE portal's `/search` endpoint with the
        given params.
        """
        query_string = "&".join(f"{i}={j}" for i, j in query_params)
        path = f"search/?{query_string}"
        return path

    def get_assembly(self, chrom_sizes_url: str) -> str:
        file = self.get_json(chrom_sizes_url)
        try:
            assembly: str = file["assembly"]
        except KeyError as e:
            raise ValueError("Chrom sizes file does not have an assembly") from e
        return assembly

    def get_url_for_file(self, file_url: str) -> str:
        file_obj = self.get_json(file_url)
        file_s3_url = self.get_url_from_file_obj(file_obj)
        return file_s3_url

    @staticmethod
    def get_url_from_file_obj(portal_file: Dict[str, Any]) -> str:
        try:
            url: str = portal_file["cloud_metadata"]["url"]
        except KeyError as e:
            raise KeyError(
                f"Could not identify cloud metadata from portal file {portal_file['@id']}"
            ) from e
        return url


class ArgHelper:
    def __init__(self) -> None:
        self._args: Optional[argparse.Namespace] = None

    @property
    def args(self) -> argparse.Namespace:
        if self._args is None:
            self._args = self.parse_args()
        return self._args

    def parse_args(self) -> argparse.Namespace:
        parser = self._get_parser()
        args = self._transform_args(parser.parse_args())
        self._validate_args(args)
        return args

    @staticmethod
    def _transform_args(args: argparse.Namespace) -> argparse.Namespace:
        epigenome_id = (
            "/".join(("reference-epigenomes", args.accession))
            if not args.accession.startswith("reference-epigenomes")
            else args.accession
        )
        args.accession = epigenome_id
        return args

    @staticmethod
    def _validate_args(args: argparse.Namespace) -> None:
        if args.skip_assays is not None:
            for assay_title in args.skip_assays:
                valid_assays = list(DATASET_OUTPUT_TYPE.keys())
                if assay_title not in valid_assays:
                    raise ValueError(
                        f"Must specify a valid assay type to skip, options are {valid_assays}"
                    )

    def get_extra_props(self, chrom_sizes_url: str, annotation_url: str) -> InputJson:
        args = vars(self.args)
        extra_props: InputJson = {k: v for k, v in args.items() if v is not None}
        extra_props.pop("accession")
        extra_props.pop("outfile", None)
        extra_props.pop("keypair", None)
        extra_props.pop("chip_targets", None)
        extra_props.pop("skip_assays", None)
        extra_props["chrom_sizes"] = chrom_sizes_url
        extra_props["annotation_gtf"] = annotation_url
        return extra_props

    def _get_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-a",
            "--accession",
            required=True,
            help="Accession of reference epigenome on the ENCODE portal",
        )
        parser.add_argument(
            "--skip-assays",
            nargs="+",
            help="Assays that should be skipped when generating input JSONs",
        )
        parser.add_argument(
            "--chip-targets",
            nargs="+",
            help="List of ChIP targets to restrict Segway input bigwigs to, e.g. H3K27ac, POL2RA",
        )
        parser.add_argument(
            "-n",
            "--num-segway-cpus",
            type=int,
            help="Number of cpus to use for Segway training and annotation, if not specified will use pipeline defaults",
        )
        parser.add_argument(
            "-r",
            "--resolution",
            type=int,
            help="Resolution, in base pairs, for Segway training, if not specified will use pipeline defaults",
        )
        parser.add_argument(
            "-f",
            "--minibatch-fraction",
            type=float,
            help="Fraction of genome to sample for each round of training, if not specified will use pipeline defaults",
        )
        parser.add_argument(
            "-m",
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
        parser.add_argument(
            "-o", "--outfile", help="Name of file to output the input JSON"
        )
        parser.add_argument(
            "-k",
            "--keypair",
            help="Path to JSON file containing portal API keys, only needed for in progress data",
        )
        return parser


def main() -> None:
    arg_helper = ArgHelper()
    args = arg_helper.args
    client = Client(keypair_path=args.keypair)
    reference_epigenome = client.get_reference_epigenome(args.accession)
    assembly = client.get_assembly(args.chrom_sizes)
    portal_files, found_targets = get_portal_files(
        reference_epigenome, assembly, client, args.skip_assays, args.chip_targets
    )
    chrom_sizes_s3_url = client.get_url_for_file(args.chrom_sizes)
    annotation_s3_url = client.get_url_for_file(args.annotation_gtf)
    extra_props = arg_helper.get_extra_props(chrom_sizes_s3_url, annotation_s3_url)
    input_json = make_input_json(portal_files, found_targets, extra_props)
    outfile = args.outfile if args.outfile is not None else f"{args.accession}.json"
    write_json(input_json, outfile)


def get_portal_files(
    reference_epigenome: Dict[str, Any],
    assembly: str,
    client: Client,
    skip_assays: Optional[List[str]] = None,
    chip_targets: Optional[List[str]] = None,
) -> List[str]:
    datasets_files: Dict[str, str] = {}
    found_targets: List[str] = []
    for dataset in reference_epigenome["related_datasets"]:
        assay_title = dataset["assay_title"]
        at_id = dataset["@id"]
        if assay_title not in DATASET_OUTPUT_TYPE.keys():
            continue
        if skip_assays is not None:
            if assay_title in skip_assays:
                continue
        if chip_targets is not None:
            if assay_title in ("Histone ChIP-seq", "TF ChIP-seq"):
                target = dataset["target"]["label"]
                if target not in chip_targets:
                    continue
                found_targets.append(target)
        bioreps = set(
            i["biological_replicate_number"]
            for i in filter_by_status(dataset["replicates"])
        )
        num_bioreps = len(bioreps)
        files = filter_by_status(dataset["original_files"])
        max_num_reps_in_files = max(len(i["biological_replicates"]) for i in files)
        is_replicated_dnase = assay_title == "DNase-seq" and num_bioreps > 1
        if is_replicated_dnase:
            preferred_replicate = get_dnase_preferred_replicate(files, client)
        for file in files:
            if file["file_format"] != "bigWig" or file["assembly"] != assembly:
                continue
            if is_replicated_dnase:
                if sorted(file["biological_replicates"]) != sorted(preferred_replicate):
                    continue
            elif len(file["biological_replicates"]) < max_num_reps_in_files:
                continue
            if file["output_type"] == DATASET_OUTPUT_TYPE[assay_title]:
                if at_id not in datasets_files:
                    datasets_files[at_id] = client.get_url_from_file_obj(file)
                else:
                    raise ValueError(
                        (
                            f"Found more than one file for dataset {at_id}: found "
                            f"{file['@id']} but already found "
                            f"{datasets_files[at_id]}"
                        )
                    )
    if chip_targets is not None:
        diff = set(chip_targets).difference(set(found_targets))
        if len(diff) != 0:
            raise ValueError(
                f"Could not find all of the specified ChIP targets in the reference epigenome provided, missing {diff}"
            )
    return list(datasets_files.values()),found_targets


def make_input_json(portal_files: List[str], found_targets: List[str], extra_props: InputJson) -> InputJson:
    input_json: InputJson = {}
    input_json[f"{WORKFLOW_NAME}.bigwigs"] = portal_files
    input_json[f"{WORKFLOW_NAME}.tracks"] = found_targets
    input_json.update({f"{WORKFLOW_NAME}.{k}": v for k, v in extra_props.items()})
    return input_json


def filter_by_status(objs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered = []
    for obj in objs:
        if obj["status"] not in EXCLUDED_STATUSES:
            filtered.append(obj)
    return filtered


def get_dnase_preferred_replicate(
    files: List[Dict[str, Any]], client: Client
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
        qc = client.get_json(samtools_flagstats[0])
        qc_mapped_read_count = qc["mapped"]
        if qc_mapped_read_count > max_mapped_read_count:
            preferred_replicate: List[int] = bam["biological_replicates"]
            max_mapped_read_count = qc_mapped_read_count
    return preferred_replicate


def write_json(input_json: InputJson, path: str) -> None:
    with open(path, "w") as f:
        f.write(json.dumps(input_json, indent=4))


if __name__ == "__main__":
    main()
