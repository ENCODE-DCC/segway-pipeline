import argparse
import csv
from typing import IO, Dict, List


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()
    with open(args.bed) as bed_file_handle, open(
        args.mnemonics
    ) as mnemonics_file_handle, open(
        args.output_filename, "w", newline=""
    ) as output_file_handle:
        relabel(bed_file_handle, mnemonics_file_handle, output_file_handle)


def relabel(
    bed_file_handle: IO[str],
    mnemonics_file_handle: IO[str],
    output_file_handle: IO[str],
) -> None:
    """
    The first row of the beds is the UCSC track definition line which should not be
    processed
    """
    mnemonics = parse_mnemonics(mnemonics_file_handle)
    input_reader = csv.reader(bed_file_handle, delimiter="\t", lineterminator="\n")
    output_writer = csv.writer(
        output_file_handle, delimiter="\t", lineterminator="\n", quotechar="'"
    )
    output_writer.writerow(next(input_reader))
    for row in input_reader:
        processed = process_row(row, mnemonics)
        output_writer.writerow(processed)


def parse_mnemonics(mnemonics_file_handle: IO[str]) -> Dict[str, str]:
    reader = csv.reader(mnemonics_file_handle, delimiter="\t", lineterminator="\n")
    mnemonics = {}
    next(reader)
    for row in reader:
        old, new = row
        mnemonics[old] = new
    return mnemonics


def process_row(row: List[str], mnemonics: Dict[str, str]) -> List[str]:
    label = row[3]
    row[3] = mnemonics[label]
    return row


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("bed")
    parser.add_argument("mnemonics")
    parser.add_argument("-o", "--output-filename", required=True)
    return parser


if __name__ == "__main__":
    main()
