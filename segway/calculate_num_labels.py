import argparse
from math import sqrt


def main():
    parser = get_parser()
    args = parser.parse_args()
    num_labels = calculate_num_labels(args.num_tracks)
    with open(args.outfile, "w") as f:
        f.write(str(num_labels))


def calculate_num_labels(num_tracks: int) -> int:
    """
    Calculates the number of labels based on the formula provided in Libbrecht et. al.
    2019, 10 + 2 * sqrt(number of tracks)
    """
    return int(10 + 2 * sqrt(num_tracks))


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-tracks", type=int, required=True)
    parser.add_argument("-o", "--outfile", required=True)
    return parser


if __name__ == "__main__":
    main()
