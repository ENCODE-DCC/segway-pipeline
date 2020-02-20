import argparse
import subprocess
from typing import List


def main():
    parser = get_parser()
    args = parser.parse_args()
    command = make_command(args.tracknames, args.files, args.sizes, args.outfile)
    run_command(command)


def make_command(
    tracknames: List[str], files: List[str], chrom_sizes: str, outfile: str
) -> List[str]:
    num_files = len(files)
    num_tracknames = len(tracknames)
    if num_files != num_tracknames:
        raise ValueError(
            (
                "Must supply same number of arguments for tracknames and files: found "
                f"{num_files} files and {num_tracknames} names"
            )
        )
    command = ["genomedata-load", "-s", chrom_sizes, "--sizes"]
    for trackname, file in zip(tracknames, files):
        command.extend(["-t", f"{trackname}={file}"])
    command.append(outfile)
    return command


def run_command(command: List[str]):
    subprocess.run(command)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--files", nargs="+", help="a list of paths to bigwig files", required=True
    )
    parser.add_argument(
        "--tracknames",
        nargs="+",
        help=(
            "a list of desired names for tracks in genomedata archive. Must be the "
            "same length as --files, and in the corresponding order"
        ),
        required=True,
    )
    parser.add_argument("--sizes", help="path to chrom sizes file", required=True)
    parser.add_argument(
        "-o", "--outfile", help="desired name of output file", required=True
    )
    return parser


if __name__ == "__main__":
    main()
