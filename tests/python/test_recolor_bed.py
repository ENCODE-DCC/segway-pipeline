from io import StringIO

import pytest

from segway_pipeline.recolor_bed import Colors, Rgb, process_row, recolor_bed


@pytest.mark.parametrize("args", [(256, 0, 0), (23, -1, 9)])
def test_rgb_invalid_input_raises(args):
    with pytest.raises(ValueError):
        Rgb(*args)


def test_rgb_str():
    color = Rgb(255, 0, 0)
    assert str(color) == "255,0,0"


def test_recolor_bed():
    labels_to_colors = {"foo": Colors.RED, "bar": Colors.ORANGE}
    bed_data = (
        "chr19\t0\t90800\t0_foo\t1000\t.\t0\t90800\t102,102,102\n"
        "chr19\t90800\t91100\t1_bar\t1000\t.\t90800\t91100\t217,95,2\n"
    )
    input_file_handle = StringIO(initial_value=bed_data)
    output_file_handle = StringIO("w", newline="")
    recolor_bed(
        input_file_handle, output_file_handle, labels_to_colors=labels_to_colors
    )
    assert output_file_handle.getvalue() == (
        "chr19\t0\t90800\t0_foo\t1000\t.\t0\t90800\t255,0,0\n"
        "chr19\t90800\t91100\t1_bar\t1000\t.\t90800\t91100\t255,195,77\n"
    )


def test_process_row():
    labels_to_colors = {"foo": Colors.RED}
    row = ["chr19", "0", "90800", "0_foo", "1000", ".", "0", "90800", "102,102,102"]
    result = process_row(row, labels_to_colors=labels_to_colors)
    assert result == [
        "chr19",
        "0",
        "90800",
        "0_foo",
        "1000",
        ".",
        "0",
        "90800",
        "255,0,0",
    ]
