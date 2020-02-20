import subprocess
from contextlib import suppress as does_not_raise
from typing import List

import pytest

from segway.make_genomedata import get_parser, main, make_command


@pytest.mark.parametrize(
    "tracknames,condition,expected",
    [
        (
            ["file1", "file2"],
            does_not_raise(),
            [
                "genomedata-load",
                "-s",
                "chrom.sizes",
                "--sizes",
                "-t",
                "file1=f1.bigwig",
                "-t",
                "file2=f2.bw",
                "my.gd",
            ],
        ),
        (["file1"], pytest.raises(ValueError), []),
    ],
)
def test_make_command(tracknames, condition, expected):
    files = ["f1.bigwig", "f2.bw"]
    sizes = "chrom.sizes"
    outfile = "my.gd"
    with condition:
        result = make_command(tracknames, files, sizes, outfile)
        assert result == expected


@pytest.mark.parametrize(
    "args,condition",
    [
        (
            [
                "--sizes",
                "ch.sizes",
                "--files",
                "a.bw",
                "b.bw",
                "--tracknames",
                "foo",
                "bar",
                "-o",
                "outfile",
            ],
            does_not_raise(),
        ),
        (
            ["--sizes", "ch.sizes", "--tracknames", "foo", "-o", "outfile"],
            pytest.raises(SystemExit),
        ),
        (
            ["--files", "b.bw", "--tracknames", "foo", "-o", "outfile"],
            pytest.raises(SystemExit),
        ),
        (
            ["--sizes", "ch.sizes", "--files", "b.bw", "--tracknames", "foo"],
            pytest.raises(SystemExit),
        ),
        (
            ["--sizes", "ch.sizes", "--files", "b.bw", "-o", "outfile"],
            pytest.raises(SystemExit),
        ),
    ],
)
def test_get_parser(args: List[str], condition):
    parser = get_parser()
    with condition:
        parser.parse_args(args)


def test_main(mocker):
    """
    The assert looks a little wonky here. The first index extracts the args of the call,
    and the second extracts the first positional arg.
    """
    mocker.patch("subprocess.run")
    testargs = [
        "prog",
        "--files",
        "ref.bw",
        "--tracknames",
        "foo",
        "--sizes",
        "chrom.sizes",
        "-o",
        "out.file",
    ]
    mocker.patch("sys.argv", testargs)
    main()
    assert subprocess.run.call_args[0] == (
        [
            "genomedata-load",
            "-s",
            "chrom.sizes",
            "--sizes",
            "-t",
            "foo=ref.bw",
            "out.file",
        ],
    )
