import argparse
import subprocess
from pathlib import Path
from typing import List


def main():
    parser = get_parser()
    args = parser.parse_args()
    command = make_command(args.files, args.tracks, args.sizes, args.outfile)
    run_command(command)


def make_command(files: List[str], tracks: str, chrom_sizes: str, outfile: str) -> List[str]:
    command = ["genomedata-load", "-s", chrom_sizes, "--sizes"]
    for file in files:
        file_basename = Path(file).with_suffix("").name
        command.extend(["-t", f"{file_basename}={file}"])
        # command.extend(["-tracks", {tracks}])
    command.append(outfile)
    return command


def run_command(command: List[str]):
    subprocess.run(command)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--files", nargs="+", help="a list of paths to bigwig files", required=True
    )
    parser.add_argument("--sizes", help="path to chrom sizes file", required=True)
    parser.add_argument(
        "-o", "--outfile", help="desired name of output file", required=True
    )
    return parser


if __name__ == "__main__":
    main()
