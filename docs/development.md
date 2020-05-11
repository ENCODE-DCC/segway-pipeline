# Developer Documentation

In order to develop this pipeline, you will first need to install the `tox` Python package. We recommend using a virtual environment to do this, such as the Python built-in library `venv`:

```bash
$ pip install tox
```

In addition, to run WDL tests, you will need to install `h5diff` to be able to compare HDF5 files. On MacOS, this can be accomplished with `brew install hdf5`. On Linux systems with the `apt` package manager, install with `sudo apt-get install hdf5-tools`.

On MacOS, you will further need to install `poppler` and `imagemagick` with `brew install poppler imagemagick` to be able to compare pdfs. If you have `apt` on Linux you can run `sudo apt-get install -y imagemagick poppler-utils`

## Running tests

To run Python tests:

```bash
$ tox -e py37
```

### Running WDL tests

Make sure to set the environment variable `SEGWAY_DOCKER_IMAGE_TAG` to point to the pipeline's docker image. Usually `quay.io/encode-dcc/segway-pipeline:template` will suffice, if your code changes require rebuilding then you will need to set this to point to the newly tagged image.

To run a WDL test with a specific tag:

```bash
$ tox -e test-wdl -- --tag test_make_genomedata
```

To preserve the output logs and files from running a WDL test, pass the `--kwd` flag:

```bash
$ tox -e test-wdl -- --tag test_make_genomedata --kwd
```

To run WDL tests in parallel, pass the `--wt` flag, here `4` indicates we want to allow a maximum of 4 workflows to execute at a time:

```bash
$ tox -e test-wdl -- --tag integration --wt 4
```

## Linting

To lint and format code, run the following:

```bash
$ tox -e lint
```
