# segway

[![Docker Repository on Quay](https://quay.io/repository/encode-dcc/segway/status "Docker Repository on Quay")](https://quay.io/repository/encode-dcc/segway)

## Description

A pipeline to run [Segway](https://segway.hoffmanlab.org/) and [Segtools](https://hoffmanlab.org/proj/segtools/) to generate chromatin segmentation models and tracks.

## Installation

1) Git clone this pipeline.
    ```bash
    $ git clone https://github.com/ENCODE-DCC/segway
    ```

2) Install [Caper](https://github.com/ENCODE-DCC/caper), requires `java` > 1.8 and `python` > 3.4.1 . Caper is a python wrapper for [Cromwell](https://github.com/broadinstitute/cromwell).
    ```bash
    $ pip install caper  # use pip3 if it doesn't work
    ```

3) Follow [Caper's README](https://github.com/ENCODE-DCC/caper) carefully to configure it for your platform (local, cloud, cluster, etc.)
    > **IMPORTANT**: Configure your Caper configuration file `~/.caper/default.conf` correctly for your platform.

## Usage

`cd` to the `segway` repository cloned in the installation, and run the following:

```bash
$ caper run segway.wdl -i ${INPUT_JSON} -o workflow_opts/docker.json -b ${BACKEND}
```

## Input Data

In the `scripts` directory there is a script to generate lists of input. It takes the ENCODE accession of a [reference epigenome](https://www.encodeproject.org/search/?type=ReferenceEpigenome) as an argument, finds the appropriate files to use as input to the model, and generates an input JSON for the pipeline. It will filter out control experiments and non-continuous datasets like WGBS and identify bigWig files on GRCh38 for each non-control experiment, preferring pooled files if the experiment is replicated. For ChIP-seq, bigWigs with the output type `fold change over control` will be selected.

To install dependencies for the scripts, make sure you have Python >= 3.5 and run `pip install -r requirements-scripts.txt`
