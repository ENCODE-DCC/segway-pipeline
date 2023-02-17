import argparse
import csv
from enum import Enum
from typing import IO, Dict, List


class Rgb:
    def __init__(self, red: int, green: int, blue: int) -> None:
        for value in (red, green, blue):
            if not 0 <= value <= 255:
                raise ValueError("Must provide RGB value between 0 and 255 inclusive")
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self) -> str:
        return f"{self.red},{self.green},{self.blue}"


class Colors(Enum):
    """
    See https://egg2.wustl.edu/roadmap/web_portal/chr_state_learning.html for color
    names and RGB values.
    """

    DARK_KHAKI = Rgb(189, 183, 107)
    GREEN = Rgb(0, 128, 0)
    GREEN_YELLOW = Rgb(196, 225, 5)
    MEDIUM_AQUAMARINE = Rgb(102, 205, 170)
    ORANGE = Rgb(255, 195, 77)
    ORANGE_RED = Rgb(255, 68, 0)
    PALE_TURQUOISE = Rgb(138, 145, 208)
    PURPLE = Rgb(128, 0, 128)
    RED = Rgb(255, 0, 0)
    SILVER = Rgb(128, 128, 128)
    WHITE = Rgb(255, 255, 255)
    YELLOW = Rgb(255, 255, 0)


LABELS_TO_COLORS = {
    "Bivalent": Colors.DARK_KHAKI,  # bivalent enhancer and bivalent TSS
    "ConstitutiveHet": Colors.PALE_TURQUOISE,  # heterochromatin
    "CTCF": Colors.GREEN_YELLOW
    "Enhancer": Colors.ORANGE,  # active enhancer
    "EnhancerLow": Colors.YELLOW,
    "FacultativeHet": Colors.PURPLE,  # polycomb repressed
    "K9K36": Colors.MEDIUM_AQUAMARINE,
    "LowConfidence": Colors.SILVER,  # no chromhmm equivalent
    "Promoter": Colors.RED,  # Active TSS
    "PromoterFlanking": Colors.ORANGE_RED,
    "Quiescent": Colors.WHITE,  # same as chromhmm
    "RegPermissive": Colors.YELLOW,  # weak enhancer
    "Transcribed": Colors.GREEN,  # strong transcription
}


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()
    with open(args.bed) as input_file_handle, open(
        args.output_filename, "w", newline=""
    ) as output_file_handle:
        recolor_bed(input_file_handle, output_file_handle)


def recolor_bed(
    input_file_handle: IO[str],
    output_file_handle: IO[str],
    labels_to_colors: Dict[str, Colors] = LABELS_TO_COLORS,
) -> None:
    input_reader = csv.reader(input_file_handle, delimiter="\t", lineterminator="\n")
    output_writer = csv.writer(
        output_file_handle, delimiter="\t", lineterminator="\n", quotechar="'"
    )
    for row in input_reader:
        processed = process_row(row, labels_to_colors=labels_to_colors)
        output_writer.writerow(processed)


def process_row(row: List[str], labels_to_colors: Dict[str, Colors]) -> List[str]:
    label = row[3]
    row[-1] = str(labels_to_colors[label.split("_")[-1]].value)
    return row


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("bed")
    parser.add_argument("-o", "--output-filename", required=True)
    return parser


if __name__ == "__main__":
    main()
