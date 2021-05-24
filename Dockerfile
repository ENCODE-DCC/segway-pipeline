FROM debian:stretch-slim@sha256:412600646303027909c65847af62841e6a08529baeb56f9bff826fe484eb6549

# Conda installation procedure lifted from https://hub.docker.com/r/continuumio/miniconda/dockerfile

LABEL maintainer "Paul Sud"
LABEL maintainer.email "encode-help@lists.stanford.edu"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH
ENV SEGTOOLS_VERSION="1.2.4"

# libkrb5-dev needed for bigWigToBedGraph generation during genomedata creation to work
RUN apt-get update && apt-get install -y \
    bzip2 \
    git \
    libkrb5-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh	 -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# segtools-signal-distribution spuriously fails with Python 3, see
# https://bitbucket.org/hoffmanlab/segtools/issues/58/segtools-signal-distribution-fails-with
RUN conda \
        install \
        -y \
        -c bioconda \
        pandas==0.25.3 \
        psutil==5.8.0 \
        segtools=="${SEGTOOLS_VERSION}" \
        segway==3.0.3 && \
    /opt/conda/bin/pip install scikit-learn==0.22.2.post1 && \
    conda install -c r r-ggplot2==3.1.1 && \
    conda create -y -n segtools-signal-distribution python=2.7 && \
    conda \
        install \
        -n segtools-signal-distribution \
        -y \
        -c bioconda \
        rpy2==2.8.6 \
        segtools=="${SEGTOOLS_VERSION}" && \
    conda clean -afy

WORKDIR /opt

RUN git clone https://github.com/marjanfarahbod/interpretation_samples.git && \
    chmod a+w interpretation_samples && \
    cd interpretation_samples && \
    git checkout aa425f56a9f671114b7a09fb35d9c3e85d40c41b && \
    rm -rf segwayOutput testworkdir model.pickle.gz && \
    chmod a+x apply_samples.py

# Needed for tests that run with non-root user
RUN chmod -R a+rwx /opt/conda/envs/segtools-signal-distribution/

# It was a pain to try to get the conda-installed bigWigToBedGraph to work. Instead we
# add the binary ourselves, and mask the conda installed binary. The conda resolver
# didn't like me trying to upgrade the ucsc-bigwigtobedgraph to 377, got conflicts.
# Possibly related: https://github.com/bioconda/bioconda-recipes/issues/14724
COPY bin/* /utils/
COPY segway_pipeline/* /software/

ENV PATH=/opt/interpretation_samples:/utils:/software:$PATH
