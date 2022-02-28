from io import StringIO

from segway_pipeline.make_trackname_assay import (
    make_trackname_assay,
    write_trackname_assay,
)


def test_make_trackname_assay():
    tracknames = ["gs://bar/foo.baz", "/qux/bar.bw"]
    assays = ["H3K27ac", "H3K4me3"]
    result = make_trackname_assay(tracknames, assays)
    assert result == [("foo", "H3K27ac"), ("bar", "H3K4me3")]


def test_make_trackname_bare_trackname():
    tracknames = ["foo", "bar"]
    assays = ["H3K27ac", "H3K4me3"]
    result = make_trackname_assay(tracknames, assays)
    assert result == [("foo", "H3K27ac"), ("bar", "H3K4me3")]


def test_write_trackname_assay():
    file_handle = StringIO("w", newline="")
    trackname_assay = [("foo", "assay1"), ("bar", "assay2")]
    write_trackname_assay(file_handle, trackname_assay)
    assert file_handle.getvalue() == "foo\tassay1\nbar\tassay2\n"
