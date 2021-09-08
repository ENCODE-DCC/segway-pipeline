import argparse
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import requests


class Assays(Enum):
    HISTONE_CHIP = "Histone ChIP-seq"
    TF_CHIP = "TF ChIP-seq"
    DNASE = "DNase-seq"
    ATAC = "ATAC-seq"


_PORTAL_URL = "https://www.encodeproject.org"
_KEYPAIR_PATH = "~/keypairs.json"
_WORKFLOW_NAME = "segway"
_CORE_TARGETS = ("H3K27ac", "H3K4me3", "H3K4me1", "H3K36me3", "H3K27me3", "H3K9me3")
_EXCLUDED_STATUSES = ("revoked", "archived", "replaced", "deleted")
_DATASET_OUTPUT_TYPE = {
    Assays.ATAC.value: "fold change over control",
    Assays.DNASE.value: "read-depth normalized signal",
    Assays.HISTONE_CHIP.value: "fold change over control",
    Assays.TF_CHIP.value: "fold change over control",
}
_ASSEMBLY_REFERENCE_FILES = {
    "GRCh38": {
        "chrom_sizes": "https://www.encodeproject.org/files/GRCh38_EBV.chrom.sizes/@@download/GRCh38_EBV.chrom.sizes.tsv",
        "annotation_gtf": "https://www.encodeproject.org/files/gencode.v29.primary_assembly.annotation_UCSC_names/@@download/gencode.v29.primary_assembly.annotation_UCSC_names.gtf.gz",
    },
    "mm10": {
        "chrom_sizes": "https://www.encodeproject.org/files/mm10_no_alt.chrom.sizes/@@download/mm10_no_alt.chrom.sizes.tsv",
        "annotation_gtf": "https://www.encodeproject.org/files/gencode.vM21.primary_assembly.annotation_UCSC_names/@@download/gencode.vM21.primary_assembly.annotation_UCSC_names.gtf.gz",
    },
}

InputJson = Dict[str, Union[float, int, str, List[str]]]


def main() -> None:
    parser = _get_parser()
    args = parser.parse_args()
    client = _get_client()
    experiments = _get_experiments_from_donor(
        client, args.donor, args.biosample_term_name
    )
    chip_targets: Optional[Iterable[str]] = None
    skip_assays: Optional[Iterable[str]] = args.skip_assays
    if args.chip_targets is not None:
        chip_targets = args.chip_targets
    if args.core_marks:
        chip_targets = _CORE_TARGETS
        skip_assays = [i.value for i in Assays if i is not Assays.HISTONE_CHIP]
    files = _get_portal_files(
        experiments,
        assembly=args.assembly,
        skip_assays=skip_assays,
        chip_targets=chip_targets,
    )
    input_json = _make_input_json(
        files, extra_props=_ASSEMBLY_REFERENCE_FILES[args.assembly]
    )
    outfile = (
        args.outfile
        if args.outfile is not None
        else f"{args.biosample_term_name.replace(' ', '_')}.json"
    )
    _write_json(input_json, outfile)


def _get_experiments_from_donor(
    client: requests.Session, donor_accession: str, biosample_term_name: str
) -> List[Dict[str, Any]]:
    biosample_query_params = {
        "type": "Biosample",
        "biosample_ontology.term_name": biosample_term_name,
        "donor.accession": donor_accession,
    }
    biosample_response = client.get(
        f"{_PORTAL_URL}/search/", params=biosample_query_params
    )
    biosample_response.raise_for_status()
    biosamples = biosample_response.json()["@graph"]
    if not biosamples:
        raise ValueError(
            f"Could not find biosamples with term name {biosample_term_name} and donor {donor_accession}"
        )
    experiment_query_params = [("type", "Experiment"), ("frame", "embedded")]
    for biosample in biosamples:
        experiment_query_params.append(
            ("replicates.library.biosample.@id", biosample["@id"])
        )
    experiment_response = client.get(
        f"{_PORTAL_URL}/search/", params=experiment_query_params
    )
    experiment_response.raise_for_status()
    experiments = experiment_response.json()["@graph"]
    if not experiments:
        raise ValueError("Could not find any experiments")
    return experiments


def _get_portal_files(
    experiments: List[Dict[str, Any]],
    assembly: str,
    skip_assays: Optional[Iterable[str]] = None,
    chip_targets: Optional[Iterable[str]] = None,
) -> List[str]:
    datasets_files: Dict[Tuple[str, ...], str] = {}
    found_targets: Set[str] = set()
    for dataset in experiments:
        assay_title = dataset["assay_title"]
        if assay_title not in _DATASET_OUTPUT_TYPE.keys():
            continue
        if dataset["status"] in _EXCLUDED_STATUSES:
            continue
        if skip_assays is not None:
            if assay_title in skip_assays:
                continue
        if chip_targets is not None:
            if assay_title in (Assays.HISTONE_CHIP.value, Assays.TF_CHIP.value):
                target = dataset["target"]["label"]
                if target not in chip_targets:
                    continue
        default_analysis = [
            i for i in dataset["analyses"] if i["@id"] == dataset["default_analysis"]
        ][0]
        for file in dataset["files"]:
            if any(
                (
                    file["file_format"] != "bigWig",
                    file.get("assembly") != assembly,
                    file["output_type"] != _DATASET_OUTPUT_TYPE[assay_title],
                    file["status"] in _EXCLUDED_STATUSES,
                    file["@id"] not in default_analysis["files"],
                )
            ):
                continue
            if file["output_type"] == _DATASET_OUTPUT_TYPE[assay_title]:
                hash_key: Tuple[str, ...] = (assay_title,)
                # For ChIP there is no preferred default fold chang over control, need
                # to check the sibling signal p-value bigwig is preferred default
                if assay_title in ("Histone ChIP-seq", "TF ChIP-seq"):
                    if not [
                        i
                        for i in dataset["files"]
                        if all(
                            (
                                i["output_type"] == "signal p-value",
                                i.get("preferred_default") is True,
                                i["biological_replicates"]
                                == file["biological_replicates"],
                            )
                        )
                    ]:
                        continue
                    target = dataset["target"]["label"]
                    hash_key = (assay_title, target)
                    found_targets.add(target)
                else:
                    if file.get("preferred_default") is not True:
                        continue
                if hash_key not in datasets_files:
                    datasets_files[hash_key] = file["cloud_metadata"]["url"]
                else:
                    raise ValueError(
                        (
                            f"Found more than one file for assay/target combination "
                            f"{','.join(hash_key)}: found {file['@id']} but already "
                            f"found {datasets_files[hash_key]}"
                        )
                    )
    if chip_targets is not None:
        diff = set(chip_targets).difference(found_targets)
        if len(diff) != 0:
            raise ValueError(
                f"Could not find all of the specified ChIP targets in the experiments provided, missing {diff}"
            )
    missing_core_targets = set(_CORE_TARGETS).difference(found_targets)
    if missing_core_targets:
        raise ValueError(
            f"Could not find one or more of the required ChIP targets in the experiments provided, missing {', '.join(missing_core_targets)}"
        )
    print(f"Found targets {', '.join(found_targets)}")
    files = list(datasets_files.values())
    if not files:
        raise ValueError("Could not find any files")
    return files


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("donor", help="The accession of the donor, e.g. ENCDO123ABC")
    parser.add_argument(
        "biosample_term_name", help="The term_name of the biosample, e.g. K562"
    )
    parser.add_argument(
        "--skip-assays",
        nargs="+",
        help="Assays that should be skipped when generating input JSONs",
    )
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--chip-targets",
        nargs="+",
        help="List of ChIP targets to restrict Segway input bigwigs to, e.g. H3K27ac, POL2RA",
    )
    target_group.add_argument(
        "--core-marks",
        help=f"Only use the 6 core histone targets {_CORE_TARGETS}",
        action="store_true",
    )
    parser.add_argument(
        "-a", "--assembly", choices=("GRCh38", "mm10"), default="GRCh38"
    )
    parser.add_argument("-o", "--outfile")
    return parser


def _get_keypair() -> Optional[Tuple[str, str]]:
    keypair_path = Path(_KEYPAIR_PATH).expanduser()
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


def _get_client() -> requests.Session:
    auth = _get_keypair()
    session = requests.Session()
    session.auth = auth
    session.headers.update({"Accept": "application/json"})
    return session


def _make_input_json(portal_files: List[str], extra_props: Dict[str, str]) -> InputJson:
    input_json: InputJson = {}
    input_json[f"{_WORKFLOW_NAME}.bigwigs"] = portal_files
    input_json.update({f"{_WORKFLOW_NAME}.{k}": v for k, v in extra_props.items()})
    return input_json


def _write_json(input_json: InputJson, path: str) -> None:
    with open(path, "w") as f:
        f.write(json.dumps(input_json, indent=2))


if __name__ == "__main__":
    main()
