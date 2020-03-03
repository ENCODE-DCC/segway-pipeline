import argparse
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import httpx

InputJson = Dict[str, Union[float, int, str, List[str]]]

PORTAL_URL = "https://www.encodeproject.org/reference-epigenomes/"
ANNOTATION_GTF = (
    "https://encode-public.s3.amazonaws.com/2019/06/04/8f6cba12-2ebe-4bec-a15d-53f49897"
    "9de0/gencode.v29.primary_assembly.annotation_UCSC_names.gtf.gz"
)
CHROM_SIZES = (
    "https://encode-public.s3.amazonaws.com/2016/01/06/89effdbe-9e3f-48c6-9781-81e565ac"
    "45a3/GRCh38_EBV.chrom.sizes.tsv"
)
WORKFLOW_NAME = "segway"


def main():
    parser = get_parser()
    args = parser.parse_args()
    url = urljoin(PORTAL_URL, args.accession)
    reference_epigenome = get_json(url)
    portal_files = get_portal_files(reference_epigenome)
    extra_props = {k: v for k, v in vars(args).items() if v is not None}
    extra_props.pop("accession")
    extra_props.pop("outfile", None)
    extra_props["chrom_sizes"] = CHROM_SIZES
    extra_props["annotation_gtf"] = ANNOTATION_GTF
    input_json = make_input_json(portal_files, extra_props)
    outfile = args.outfile
    if args.outfile is None:
        outfile = f"{args.accession}.json"
    write_json(input_json, outfile)


def get_portal_files(reference_epigenome: Dict[str, Any]) -> List[str]:
    dataset_output_type = {
        "TF ChIP-seq": "fold change over control",
        "Histone ChIP-seq": "fold change over control",
        "DNase-seq": "read-depth normalized signal",
    }
    datasets_files: Dict[str, str] = {}
    for dataset in reference_epigenome["related_datasets"]:
        assay_title = dataset["assay_title"]
        at_id = dataset["@id"]
        if assay_title not in dataset_output_type.keys():
            continue
        num_bioreps = len(
            set(i["biological_replicate_number"] for i in dataset["replicates"])
        )
        for file in dataset["files"]:
            if (
                file["file_format"] != "bigWig"
                or file["assembly"] != "GRCh38"
                or len(file["biological_replicates"]) < num_bioreps
            ):
                continue
            if file["output_type"] == dataset_output_type[assay_title]:
                if at_id not in datasets_files:
                    datasets_files[at_id] = file["cloud_metadata"]["url"]
                else:
                    raise ValueError(
                        (
                            f"Found more than one file for dataset {at_id}: found "
                            f"{file['@id']} but already found {datasets_files[at_id]}"
                        )
                    )
    return list(datasets_files.values())


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
    parser.add_argument("-o", "--outfile")
    return parser


if __name__ == "__main__":
    main()
