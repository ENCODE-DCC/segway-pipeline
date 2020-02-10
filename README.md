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

```bash
$ caper run segway.wdl -i ${INPUT_JSON}
```
