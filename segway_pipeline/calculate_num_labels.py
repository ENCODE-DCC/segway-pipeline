import argparse
from math import sqrt


def main():
    parser = get_parser()
    print("The value of parser in calculate_num_labels is: ")
    print(parser)
    args = parser.parse_args()
    print("The value of args in calculate_num_labels is: ")
    print(args)
    num_labels = calculate_num_labels(args.num_tracks)
    print("The value of num_labels in calculate_num_labels is: ")
    print(num_labels)
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
