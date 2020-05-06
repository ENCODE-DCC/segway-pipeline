# segway

[![CircleCI](https://circleci.com/gh/ENCODE-DCC/segway-pipeline/tree/dev.svg?style=svg)](https://circleci.com/gh/ENCODE-DCC/segway-pipeline/tree/dev)
[![Docker Repository on Quay](https://quay.io/repository/encode-dcc/segway-pipeline/status "Docker Repository on Quay")](https://quay.io/repository/encode-dcc/segway-pipeline)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Description

A pipeline to run [Segway](https://segway.hoffmanlab.org/) and [Segtools](https://hoffmanlab.org/proj/segtools/) to generate chromatin segmentation models and tracks.

## Installation

1) Git clone this pipeline.
    ```bash
    $ git clone https://github.com/ENCODE-DCC/segway-pipeline.git
    ```

2) Install [Caper](https://github.com/ENCODE-DCC/caper), requires `java` > 1.8 and `python` > 3.4.1 . Caper is a python wrapper for [Cromwell](https://github.com/broadinstitute/cromwell).
    ```bash
    $ pip install caper  # use pip3 if it doesn't work
    ```

3) Follow [Caper's README](https://github.com/ENCODE-DCC/caper) carefully to configure it for your platform (local, cloud, cluster, etc.)
    > **IMPORTANT**: Configure your Caper configuration file `~/.caper/default.conf` correctly for your platform.

## Usage

`cd` to the `segway-pipeline` repository cloned in the installation, and run the following:

```bash
$ caper run segway.wdl -i ${INPUT_JSON} -o workflow_opts/docker.json -b ${BACKEND}
```

## Input Data

In the `scripts` directory there is a script to generate lists of input. It takes the ENCODE accession of a [reference epigenome](https://www.encodeproject.org/search/?type=ReferenceEpigenome) as an argument, finds the appropriate files to use as input to the model, and generates an input JSON for the pipeline. It will filter out control experiments and non-continuous datasets like WGBS and identify bigWig files on GRCh38 for each non-control experiment, preferring pooled files if the experiment is replicated. For ChIP-seq and ATAC-seq, bigWigs with the output type `fold change over control` will be selected. For DNase datasets, the `read-depth normalized signal` bigWig from the replicate with the greatest number of mapped reads after filtering will be selected.

To install dependencies for the scripts, make sure you have Python >= 3.5 and run `pip install -r requirements-scripts.txt`

An example usage is given below. The values for `--chrom-sizes` and `--annotation-gtf` are IDs for file objects at the portal, e.g. https://www.encodeproject.org/files/GRCh38_EBV.chrom.sizes . The assays to skip specified by `--skip-assays` should be quoted to avoid being consumed as separate arguments if there are spaces in them. The `--chip-targets` correspond to an experiment's `target.label` property, and can be either histone or TF targets. An error will be raised if no matching targets were found for the given reference epigenome.

```bash
python scripts/make_input_jsons_from_portal.py --chrom-sizes GRCh38_EBV.chrom.sizes --annotation-gtf gencode.v29.primary_assembly.annotation_UCSC_names  --skip-assays "TF ChIP-seq" --chip-targets H3K4me3 H3K27ac -a ENCSR867OGI
```

## Development

See the [developer docs](docs/development.md) for more details on running tests and developing this pipeline.
