import subprocess
from contextlib import suppress as does_not_raise
from typing import List

import pytest

from segway_pipeline.make_genomedata import get_parser, main, make_command


def test_make_command():
    files = ["f1.bigwig", "f2.bw"]
    sizes = "chrom.sizes"
    tracks = ["track1.H3K4me1", "track2.H3K4me3"]
    outfile = "my.gd"
    result = make_command(files, sizes, tracks, outfile)
    assert result == [
        "genomedata-load",
        "-s",
        "chrom.sizes",
        "--sizes",
        "-t",
        "f1=f1.bigwig",
        "-t",
        "f2=f2.bw",
        "-tracks",
        "track1.H3K4me1",
        "-tracks",
        "track2.H3K4me3",
        "my.gd",
    ]


@pytest.mark.parametrize(
    "args,condition",
    [
        (["--sizes", "ch.sizes", "--files", "b.bw", "--tracks", "H3K4me3", "-o", "outfile"], does_not_raise()),
        (["--sizes", "ch.sizes", "-o", "outfile"], pytest.raises(SystemExit)),
        (["--files", "b.bw", "-o", "outfile"], pytest.raises(SystemExit)),
        (["--sizes", "ch.sizes", "--files", "b.bw"], pytest.raises(SystemExit)),
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
        "--sizes",
        "chrom.sizes",
        "--tracks",
        "H3K4me1",
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
            "ref=ref.bw",
            "-tracks",
            "H3K4me1",
            "out.file",
        ],
    )
