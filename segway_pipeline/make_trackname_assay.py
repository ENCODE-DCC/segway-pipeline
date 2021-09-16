import argparse
import csv
from pathlib import Path
from typing import IO, List, Tuple


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()
    trackname_assay = make_trackname_assay(args.tracknames, args.assays)
    with open(args.output_filename, "w", newline="") as f:
        write_trackname_assay(f, trackname_assay)


def make_trackname_assay(
    tracknames: List[str], assays: List[str]
) -> List[Tuple[str, str]]:
    return [
        (Path(trackname).stem, assay) for trackname, assay in zip(tracknames, assays)
    ]


def write_trackname_assay(
    file_handle: IO[str], trackname_assay: List[Tuple[str, str]]
) -> None:
    writer = csv.writer(file_handle, delimiter="\t", lineterminator="\n")
    writer.writerows(trackname_assay)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracknames", nargs="+", required=True)
    parser.add_argument("--assays", nargs="+", required=True)
    parser.add_argument("--output-filename", required=True)
    return parser


if __name__ == "__main__":
    main()
