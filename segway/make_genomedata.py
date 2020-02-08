import argparse
from pathlib import Path
import subprocess
from typing import List


def main():
    parser = get_parser()
    args = parser.parse_args()
    command = make_command(args.files, args.sizes)
    run_command(command)


def make_command(files: List[str], chrom_sizes: str) -> List[str]:
    command = ["genomedata-load", "-s", chrom_sizes, "--sizes"]
    for file in files:
        file_basename = Path(file).with_suffix("").name
        command.extend(["-t", f"{file_basename}=file"])
    return command


def run_command(command: List[str]):
    subprocess.run(command)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", help="a list of paths to bigwig files")
    parser.add_argument("--sizes", help="path to chrom sizes file")
    return parser


if __name__ == "__main__":
    main()
