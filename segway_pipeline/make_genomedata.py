import argparse
import subprocess
from pathlib import Path
from typing import List


def main():
    parser = get_parser()
    print("Value of Parser is: ")
    print(parser)
    args = parser.parse_args()
    print("Value of Args is: ")
    print(args)
    command = make_command(args.files, args.track_labels, args.sizes, args.outfile)
    print("Value of Command is: ")
    print(command)
    run_command(command)


def make_command(files: List[str], track_labels: List[str], chrom_sizes: str, outfile: str) -> List[str]:
    command = ["genomedata-load", "-s", chrom_sizes, "--sizes"]
    for file in files:
        file_basename = Path(file).with_suffix("").name
        command.extend(["-t", f"{file_basename}={file}"])
        command.extend(["-track_labels", {track_labels}])
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
