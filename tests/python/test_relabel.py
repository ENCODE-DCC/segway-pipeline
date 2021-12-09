from io import StringIO

import pytest

from segway_pipeline.relabel import parse_mnemonics, process_row, relabel


@pytest.fixture
def mnemonics_file_handle():
    return StringIO(initial_value="old\tnew\n0\tfoo\n1\tbar\n")


def test_relabel(mnemonics_file_handle):
    bed_data = (
        "chr19\t0\t90800\t0\t1000\t.\t0\t90800\t102,102,102\n"
        "chr19\t90800\t91100\t1\t1000\t.\t90800\t91100\t217,95,2\n"
    )
    bed_file_handle = StringIO(initial_value=bed_data)
    output_file_handle = StringIO("w", newline="")
    relabel(bed_file_handle, mnemonics_file_handle, output_file_handle)
    assert output_file_handle.getvalue() == (
        "chr19\t0\t90800\tfoo\t1000\t.\t0\t90800\t102,102,102\n"
        "chr19\t90800\t91100\tbar\t1000\t.\t90800\t91100\t217,95,2\n"
    )


def test_parse_mnemonics(mnemonics_file_handle):
    result = parse_mnemonics(mnemonics_file_handle)
    assert result == {"0": "foo", "1": "bar"}


def test_process_row():
    mnemonics = {"0": "foo"}
    row = ["chr19", "0", "90800", "0", "1000", ".", "0", "90800", "102,102,102"]
    result = process_row(row, mnemonics=mnemonics)
    assert result == [
        "chr19",
        "0",
        "90800",
        "foo",
        "1000",
        ".",
        "0",
        "90800",
        "102,102,102",
    ]
