import argparse
import builtins
from contextlib import suppress as does_not_raise
from typing import List

import httpx
import pytest
import respx

from scripts.make_input_jsons_from_portal import (
    UrlJoiner,
    filter_by_status,
    get_assembly,
    get_dnase_preferred_replicate,
    get_extra_props_from_args,
    get_json,
    get_keypair,
    get_parser,
    get_portal_files,
    get_url_from_file_obj,
    main,
    make_input_json,
    validate_args,
    write_json,
)


@pytest.fixture
def urljoiner():
    return UrlJoiner("https://www.qux.io/")


@pytest.fixture
def assembly():
    return "GRCh38"


def test_urljoiner_init():
    base_url = "http://foo.biz/"
    urljoiner = UrlJoiner(base_url)
    assert not urljoiner.base_is_valid


@pytest.mark.parametrize(
    "condition,base_url",
    [
        (does_not_raise(), "http://foo.bar/"),
        (pytest.raises(ValueError), "http://base.com"),
    ],
)
def test_urljoiner_validate_base_url(urljoiner, condition, base_url):
    with condition:
        urljoiner.validate_base_url(base_url)


def test_urljoiner_base_url(urljoiner):
    assert urljoiner.base_url == "https://www.qux.io/"
    assert urljoiner.base_is_valid


def test_urljoiner_resolve(urljoiner):
    result = urljoiner.resolve("path")
    assert result == "https://www.qux.io/path"


@respx.mock
def test_main(mocker):
    mocker.patch(
        "sys.argv",
        [
            "prog",
            "-a",
            "my_accession",
            "-f",
            "0.1",
            "-m",
            "5",
            "-g",
            "gtf",
            "-c",
            "sizes",
        ],
    )
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(
        "scripts.make_input_jsons_from_portal.get_assembly", return_value="GRCh38"
    )
    content = {
        "related_datasets": [
            {
                "@id": "exp1",
                "assay_title": "TF ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "files": [
                    {
                        "@id": "tf_chip_1",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "cloud_metadata": {"url": "https://d.na/tf_chip_1"},
                        "status": "released",
                    }
                ],
            }
        ]
    }
    respx.get(
        "https://www.encodeproject.org/sizes",
        content={"assembly": "GRCh38", "cloud_metadata": {"url": "bar"}},
        status_code=200,
    )
    respx.get(
        "https://www.encodeproject.org/gtf",
        content={"cloud_metadata": {"url": "foo"}},
        status_code=200,
    )
    respx.get(
        "https://www.encodeproject.org/reference-epigenomes/my_accession",
        content=content,
        status_code=200,
    )
    main()
    assert builtins.open.mock_calls[2][1][0] == (
        '{\n    "segway.bigwigs": [\n        "https://d.na/tf_chip_1"\n    ],\n    "seg'
        'way.minibatch_fraction": 0.1,\n    "segway.max_train_rounds": 5,\n    "segway.'
        'annotation_gtf": "foo",\n    "segway.chrom_sizes": "bar"\n}'
    )


@pytest.mark.parametrize(
    "condition,skip_assays",
    [(does_not_raise(), ["DNase-seq"]), (pytest.raises(ValueError), ["DNase"])],
)
def test_validate_args(condition, skip_assays):
    args = argparse.Namespace()
    args.skip_assays = skip_assays
    with condition:
        validate_args(args)


@pytest.mark.parametrize(
    "condition,reference_epigenome,assembly,expected",
    [
        (
            does_not_raise(),
            {
                "related_datasets": [
                    {
                        "@id": "exp1",
                        "assay_title": "TF ChIP-seq",
                        "replicates": [
                            {"biological_replicate_number": 1, "status": "released"},
                            {"biological_replicate_number": 3, "status": "released"},
                        ],
                        "files": [
                            {
                                "@id": "tf_chip_1",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "cloud_metadata": {"url": "https://d.na/tf_chip_1"},
                                "status": "released",
                            },
                            {
                                "@id": "tf_chip_2",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [3],
                                "status": "released",
                            },
                            {
                                "@id": "tf_chip_3",
                                "assembly": "hg19",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "status": "released",
                            },
                            {
                                "@id": "tf_chip_4",
                                "assembly": "GRCh38",
                                "output_type": "signal p-value",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "status": "released",
                            },
                        ],
                    },
                    {
                        "@id": "exp2",
                        "assay_title": "Histone ChIP-seq",
                        "replicates": [
                            {"biological_replicate_number": 1, "status": "released"}
                        ],
                        "files": [
                            {
                                "@id": "histone_chip_1",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1],
                                "cloud_metadata": {
                                    "url": "https://d.na/histone_chip_1"
                                },
                                "status": "released",
                            }
                        ],
                    },
                    {
                        "@id": "atac",
                        "assay_title": "ATAC-seq",
                        "replicates": [
                            {"biological_replicate_number": 1, "status": "released"}
                        ],
                        "files": [
                            {
                                "@id": "atac_1",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1],
                                "cloud_metadata": {"url": "https://a.tac/1"},
                                "status": "released",
                            }
                        ],
                    },
                    {
                        "@id": "exp3",
                        "assay_title": "DNase-seq",
                        "replicates": [
                            {"biological_replicate_number": 1, "status": "released"}
                        ],
                        "files": [
                            {
                                "@id": "dnase",
                                "assembly": "GRCh38",
                                "output_type": "read-depth normalized signal",
                                "file_format": "bigWig",
                                "biological_replicates": [1],
                                "cloud_metadata": {"url": "https://d.na/dnase"},
                                "status": "released",
                            }
                        ],
                    },
                    {"@id": "exp4", "assay_title": "WGBS"},
                ]
            },
            "GRCh38",
            [
                "https://d.na/tf_chip_1",
                "https://d.na/histone_chip_1",
                "https://d.na/dnase",
                "https://a.tac/1",
            ],
        ),
        (
            does_not_raise(),
            {
                "related_datasets": [
                    {
                        "@id": "exp3",
                        "assay_title": "DNase-seq",
                        "replicates": [
                            {"biological_replicate_number": 1, "status": "released"},
                            {"biological_replicate_number": 2, "status": "released"},
                        ],
                        "files": [
                            {
                                "@id": "bam1",
                                "output_type": "alignments",
                                "file_format": "bam",
                                "biological_replicates": [1],
                                "quality_metrics": [
                                    "/samtools-flagstats-quality-metrics/1/"
                                ],
                                "status": "released",
                            },
                            {
                                "@id": "bam2",
                                "output_type": "alignments",
                                "file_format": "bam",
                                "biological_replicates": [2],
                                "quality_metrics": [
                                    "/samtools-flagstats-quality-metrics/2/"
                                ],
                                "status": "released",
                            },
                            {
                                "@id": "dnase",
                                "assembly": "GRCh38",
                                "output_type": "read-depth normalized signal",
                                "file_format": "bigWig",
                                "biological_replicates": [1],
                                "cloud_metadata": {"url": "https://d.na/dnase"},
                                "status": "released",
                            },
                            {
                                "@id": "dnase2",
                                "assembly": "GRCh38",
                                "output_type": "read-depth normalized signal",
                                "file_format": "bigWig",
                                "biological_replicates": [2],
                                "cloud_metadata": {"url": "https://d.na/dnase2"},
                                "status": "released",
                            },
                        ],
                    }
                ]
            },
            "GRCh38",
            ["https://d.na/dnase"],
        ),
        (
            pytest.raises(ValueError),
            {
                "related_datasets": [
                    {
                        "@id": "exp1",
                        "assay_title": "TF ChIP-seq",
                        "replicates": [
                            {"biological_replicate_number": 1, "status": "released"},
                            {"biological_replicate_number": 3, "status": "released"},
                        ],
                        "files": [
                            {
                                "@id": "tf_chip_1",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "cloud_metadata": {"url": "https://d.na/tf_chip_1"},
                                "status": "released",
                            },
                            {
                                "@id": "tf_chip_2",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "status": "released",
                            },
                        ],
                    }
                ]
            },
            "GRCh38",
            [],
        ),
    ],
)
@respx.mock
def test_get_portal_files(
    urljoiner, condition, reference_epigenome, assembly, expected
):
    respx.get(
        urljoiner.resolve("/samtools-flagstats-quality-metrics/1/"),
        content={"mapped": 10},
        status_code=200,
    )
    respx.get(
        urljoiner.resolve("/samtools-flagstats-quality-metrics/2/"),
        content={"mapped": 2},
        status_code=200,
    )
    with condition:
        result = get_portal_files(reference_epigenome, assembly, urljoiner)
        assert sorted(result) == sorted(expected)


def test_get_portal_files_chip_targets(urljoiner, assembly):
    reference_epigenome = {
        "related_datasets": [
            {
                "@id": "exp3",
                "assay_title": "Histone ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "target": {"label": "H3K27ac"},
                "files": [
                    {
                        "@id": "file1",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "status": "released",
                        "cloud_metadata": {"url": "https://file.1"},
                    }
                ],
            },
            {
                "@id": "exp4",
                "assay_title": "TF ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "target": {"label": "EP300"},
                "files": [
                    {
                        "@id": "file2",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "status": "released",
                        "cloud_metadata": {"url": "https://file.2"},
                    }
                ],
            },
            {
                "@id": "exp4",
                "assay_title": "TF ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "target": {"label": "NANOG"},
                "files": [
                    {
                        "@id": "file3",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "status": "released",
                        "cloud_metadata": {"url": "https://file.3"},
                    }
                ],
            },
        ]
    }
    result = get_portal_files(
        reference_epigenome, assembly, urljoiner, chip_targets=["H3K27ac", "EP300"]
    )
    assert sorted(result) == sorted(["https://file.1", "https://file.2"])


def test_get_portal_files_missing_chip_target_raises(urljoiner, assembly):
    reference_epigenome = {
        "related_datasets": [
            {
                "@id": "exp3",
                "assay_title": "Histone ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "target": {"label": "H3K27ac"},
                "files": [
                    {
                        "@id": "file1",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "status": "released",
                        "cloud_metadata": {"url": "https://file.1"},
                    }
                ],
            }
        ]
    }
    with pytest.raises(ValueError):
        get_portal_files(reference_epigenome, assembly, urljoiner, chip_targets=["foo"])


def test_get_portal_files_skip_assays(urljoiner, assembly):
    reference_epigenome = {
        "related_datasets": [
            {
                "@id": "exp3",
                "assay_title": "Histone ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "target": {"label": "H3K27ac"},
                "files": [
                    {
                        "@id": "file1",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "status": "released",
                        "cloud_metadata": {"url": "https://file.1"},
                    }
                ],
            },
            {
                "@id": "exp4",
                "assay_title": "TF ChIP-seq",
                "replicates": [
                    {"biological_replicate_number": 1, "status": "released"}
                ],
                "target": {"label": "EP300"},
                "files": [
                    {
                        "@id": "file2",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "status": "released",
                        "cloud_metadata": {"url": "https://file.2"},
                    }
                ],
            },
        ]
    }
    result = get_portal_files(
        reference_epigenome, assembly, urljoiner, skip_assays=["TF ChIP-seq"]
    )
    assert result == ["https://file.1"]


@pytest.mark.parametrize(
    "condition,path,read_data,expected",
    [
        (does_not_raise(), None, "{}", None),
        (
            does_not_raise(),
            "foo.json",
            '{"submit": {"key": "foo", "secret": "bar"}}',
            ("foo", "bar"),
        ),
        (pytest.raises(KeyError), "bar.json", '{"server": "wrong"}', ()),
    ],
)
def test_get_keypair(mocker, condition, path, read_data, expected):
    mocker.patch("builtins.open", mocker.mock_open(read_data=read_data))
    with condition:
        result = get_keypair(path)
        assert result == expected


def test_get_extra_props_from_args():
    args = {"accession": "foo", "outfile": "bar", "keypair": "baz", "extra": 3}
    chrom_sizes_url = "www.chrom.sizes"
    annotation_url = "annotation.url"
    result = get_extra_props_from_args(args, chrom_sizes_url, annotation_url)
    assert result == {
        "annotation_gtf": "annotation.url",
        "chrom_sizes": "www.chrom.sizes",
        "extra": 3,
    }


@pytest.mark.parametrize(
    "condition, content,expected",
    [
        (does_not_raise(), {"assembly": "GRCh38"}, "GRCh38"),
        (pytest.raises(ValueError), {"@id": "foo"}, ""),
    ],
)
@respx.mock
def test_get_assembly(condition, content, expected):
    url = "https://www.encodeproject.org/assembly"
    respx.get(url, content=content, status_code=200)
    with condition:
        result = get_assembly(url)
        assert result == expected


def test_make_input_json():
    portal_files = ["http://foo.bar/f1", "http://foo.bar/f2"]
    kwargs = {"prior_strength": 1.5, "num_segway_cpus": 10}
    result = make_input_json(portal_files, kwargs)
    assert result == {
        "segway.bigwigs": ["http://foo.bar/f1", "http://foo.bar/f2"],
        "segway.num_segway_cpus": 10,
        "segway.prior_strength": 1.5,
    }


@pytest.mark.parametrize(
    "condition,status_code,content",
    [
        (does_not_raise(), 200, {"foo": "bar"}),
        (pytest.raises(TypeError), 200, ["foo"]),
        (pytest.raises(httpx.HTTPError), 404, {}),
    ],
)
@respx.mock
def test_get_json(condition, status_code, content):
    url = "https://www.encodeproject.org/data"
    with condition:
        respx.get(url, content=content, status_code=status_code)
        data = get_json(url)
        assert data == content


@pytest.mark.parametrize(
    "condition,obj,expected",
    [
        (does_not_raise(), {"cloud_metadata": {"url": "foo"}}, "foo"),
        (pytest.raises(KeyError), {}, ""),
    ],
)
def test_get_url_from_file_obj(condition, obj, expected):
    with condition:
        result = get_url_from_file_obj(obj)
        assert result == expected


def test_filter_by_status():
    objs = [{"status": "released"}, {"status": "revoked"}]
    result = filter_by_status(objs)
    assert result == [{"status": "released"}]


@pytest.mark.parametrize(
    "condition,files,expected",
    [
        (
            does_not_raise(),
            [
                {
                    "output_type": "alignments",
                    "biological_replicates": [1],
                    "quality_metrics": [
                        "/samtools-flagstats-quality-metrics/1/",
                        "/other/bar/",
                    ],
                },
                {
                    "output_type": "alignments",
                    "biological_replicates": [2],
                    "quality_metrics": ["/samtools-flagstats-quality-metrics/2/"],
                },
            ],
            [1],
        ),
        (
            pytest.raises(ValueError),
            [
                {
                    "@id": "foo",
                    "output_type": "alignments",
                    "biological_replicates": [1],
                    "quality_metrics": [
                        "/samtools-flagstats-quality-metrics/1/",
                        "/samtools-flagstats-quality-metrics/2/",
                    ],
                }
            ],
            [1],
        ),
        (
            pytest.raises(ValueError),
            [
                {
                    "@id": "foo",
                    "output_type": "alignments",
                    "biological_replicates": [1],
                    "quality_metrics": [],
                }
            ],
            [1],
        ),
    ],
)
@respx.mock
def test_get_dnase_preferred_replicate(urljoiner, condition, files, expected):
    respx.get(
        urljoiner.resolve("/samtools-flagstats-quality-metrics/1/"),
        content={"mapped": 10},
        status_code=200,
    )
    respx.get(
        urljoiner.resolve("/samtools-flagstats-quality-metrics/2/"),
        content={"mapped": 2},
        status_code=200,
    )
    with condition:
        result = get_dnase_preferred_replicate(files, urljoiner)
        assert result == expected


def test_write_json(mocker):
    mocker.patch("builtins.open", mocker.mock_open())
    input_json = {"foo": "bar"}
    write_json(input_json, "path")
    assert builtins.open.mock_calls[2][1][0] == '{\n    "foo": "bar"\n}'


@pytest.mark.parametrize(
    "args,condition",
    [
        (["-a", "accession", "-g", "gtf", "-c", "sizes"], does_not_raise()),
        (["-a", "accession", "-c", "sizes"], pytest.raises(SystemExit)),
        (["-a", "accession", "-g", "gtf"], pytest.raises(SystemExit)),
        (["-o", "outfile"], pytest.raises(SystemExit)),
    ],
)
def test_get_parser(args: List[str], condition):
    parser = get_parser()
    with condition:
        parser.parse_args(args)
