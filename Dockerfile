FROM debian:stretch-slim@sha256:412600646303027909c65847af62841e6a08529baeb56f9bff826fe484eb6549

# Conda installation procedure lifted from https://hub.docker.com/r/continuumio/miniconda/dockerfile

LABEL maintainer "Paul Sud"
LABEL maintainer.email "encode-help@lists.stanford.edu"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

# libkrb5-dev needed for bigWigToBedGraph generation during genomedata creation to work
RUN apt-get update && apt-get install -y \
    bzip2 \
    libkrb5-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# TODO: pin versions of segway and segtools
RUN conda install -y -c bioconda pandas scikit-learn segway segtools && conda clean -afy

RUN wget https://bitbucket.org/mlibbrecht/saga_interpretation/raw/f463f97a3e517c1f62f5a1f9003014686ba06c14/saga_interpretation.py && \
    chmod +x saga_interpretation.py && \
    mkdir /software && \
    mv saga_interpretation.py /software

# It was a pain to try to get the conda-installed bigWigToBedGraph to work. Instead we
# add the binary ourselves, and mask the conda installed binary. The conda resolver
# didn't like me trying to upgrade the ucsc-bigwigtobedgraph to 377, got conflicts.
# Possibly related: https://github.com/bioconda/bioconda-recipes/issues/14724
COPY bin/* /utils/
COPY segway/* /software/

ENV PATH=/utils:/software:$PATH
