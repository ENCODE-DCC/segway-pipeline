import builtins
import re
from contextlib import suppress as does_not_raise
from typing import List

import httpx
import pytest
import respx

from scripts.make_input_jsons_from_portal import (
    get_json,
    get_parser,
    get_portal_files,
    main,
    make_input_json,
    write_json,
)


@respx.mock
def test_main(mocker):
    mocker.patch("sys.argv", ["prog", "-a", "my_accession", "-f", "0.1", "-r", "5"])
    mocker.patch("builtins.open", mocker.mock_open())
    content = {
        "related_datasets": [
            {
                "@id": "exp1",
                "assay_title": "TF ChIP-seq",
                "replicates": [{"biological_replicate_number": 1}],
                "files": [
                    {
                        "@id": "tf_chip_1",
                        "assembly": "GRCh38",
                        "output_type": "fold change over control",
                        "file_format": "bigWig",
                        "biological_replicates": [1],
                        "cloud_metadata": {"url": "https://d.na/tf_chip_1"},
                    }
                ],
            }
        ]
    }
    url_pattern = re.compile(r"^https://www.encodeproject.org/.*$")
    respx.get(url_pattern, content=content, status_code=200)
    main()
    assert respx.calls[0][0].url == (
        "https://www.encodeproject.org/reference-epigenomes/my_accession"
    )
    assert builtins.open.mock_calls[2][1][0] == (
        '{\n    "segway.bigwigs": [\n        "https://d.na/tf_chip_1"\n    ],\n    "seg'
        'way.minibatch_fraction": 0.1,\n    "segway.max_train_rounds": 5,\n    "segway.'
        'chrom_sizes": "https://encode-public.s3.amazonaws.com/2016/01/06/89effdbe-9e3f'
        '-48c6-9781-81e565ac45a3/GRCh38_EBV.chrom.sizes.tsv",\n    "segway.annotation_g'
        'tf": "https://encode-public.s3.amazonaws.com/2019/06/04/8f6cba12-2ebe-4bec-a15'
        'd-53f498979de0/gencode.v29.primary_assembly.annotation_UCSC_names.gtf.gz"\n}'
    )


@pytest.mark.parametrize(
    "condition,reference_epigenome,expected",
    [
        (
            does_not_raise(),
            {
                "related_datasets": [
                    {
                        "@id": "exp1",
                        "assay_title": "TF ChIP-seq",
                        "replicates": [
                            {"biological_replicate_number": 1},
                            {"biological_replicate_number": 3},
                        ],
                        "files": [
                            {
                                "@id": "tf_chip_1",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "cloud_metadata": {"url": "https://d.na/tf_chip_1"},
                            },
                            {
                                "@id": "tf_chip_2",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [3],
                            },
                            {
                                "@id": "tf_chip_3",
                                "assembly": "hg19",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                            },
                            {
                                "@id": "tf_chip_4",
                                "assembly": "GRCh38",
                                "output_type": "signal p-value",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                            },
                        ],
                    },
                    {
                        "@id": "exp2",
                        "assay_title": "Histone ChIP-seq",
                        "replicates": [{"biological_replicate_number": 1}],
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
                            }
                        ],
                    },
                    {
                        "@id": "exp3",
                        "assay_title": "DNase-seq",
                        "replicates": [{"biological_replicate_number": 1}],
                        "files": [
                            {
                                "@id": "dnase",
                                "assembly": "GRCh38",
                                "output_type": "read-depth normalized signal",
                                "file_format": "bigWig",
                                "biological_replicates": [1],
                                "cloud_metadata": {"url": "https://d.na/dnase"},
                            }
                        ],
                    },
                    {"@id": "exp4", "assay_title": "WGBS"},
                ]
            },
            [
                "https://d.na/tf_chip_1",
                "https://d.na/histone_chip_1",
                "https://d.na/dnase",
            ],
        ),
        (
            pytest.raises(ValueError),
            {
                "related_datasets": [
                    {
                        "@id": "exp1",
                        "assay_title": "TF ChIP-seq",
                        "replicates": [
                            {"biological_replicate_number": 1},
                            {"biological_replicate_number": 3},
                        ],
                        "files": [
                            {
                                "@id": "tf_chip_1",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                                "cloud_metadata": {"url": "https://d.na/tf_chip_1"},
                            },
                            {
                                "@id": "tf_chip_2",
                                "assembly": "GRCh38",
                                "output_type": "fold change over control",
                                "file_format": "bigWig",
                                "biological_replicates": [1, 3],
                            },
                        ],
                    }
                ]
            },
            [],
        ),
    ],
)
def test_get_portal_files(condition, reference_epigenome, expected):
    with condition:
        result = get_portal_files(reference_epigenome)
        assert sorted(result) == sorted(expected)


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
        (pytest.raises(httpx.exceptions.HTTPError), 404, {}),
    ],
)
@respx.mock
def test_get_json(condition, status_code, content):
    url = "https://www.encodeproject.org/data"
    with condition:
        respx.get(url, content=content, status_code=status_code)
        data = get_json(url)
        assert data == content


def test_write_json(mocker):
    mocker.patch("builtins.open", mocker.mock_open())
    input_json = {"foo": "bar"}
    write_json(input_json, "path")
    assert builtins.open.mock_calls[2][1][0] == '{\n    "foo": "bar"\n}'


@pytest.mark.parametrize(
    "args,condition",
    [
        (["-a", "accession"], does_not_raise()),
        (["-o", "outfile"], pytest.raises(SystemExit)),
    ],
)
def test_get_parser(args: List[str], condition):
    parser = get_parser()
    with condition:
        parser.parse_args(args)
