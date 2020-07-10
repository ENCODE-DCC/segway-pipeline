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
    libkrb5-dev \
    libssl-dev \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh	 -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN git clone https://github.com/ENCODE-DCC/kentUtils_bin_v377.git  && \
    chmod +x kentUtils_bin_v377/bin/bedToBigBed && \
    mv kentUtils_bin_v377/bin/bedToBigBed /usr/local/bin/ && \
    rm -rf kentUtils_bin_v377

# segtools-signal-distribution spuriously fails with Python 3, see
# https://bitbucket.org/hoffmanlab/segtools/issues/58/segtools-signal-distribution-fails-with
RUN conda install -y -c bioconda segway==3.0 segtools=="${SEGTOOLS_VERSION}" numpy==1.16.4 && \
    conda create -y -n segtools-signal-distribution python=2.7 && \
    conda install -n segtools-signal-distribution -y -c bioconda segtools=="${SEGTOOLS_VERSION}" && \
    conda clean -afy

RUN wget -q https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/bedToBigBed -O /utils/bedToBigBed  && \
    chmod +x /utils/bedToBigBed && \
    cp /utils/bedToBigBed /usr/local/bin/bedToBigBed && \
    cp /utils/bedToBigBed /opt/conda/bin/bedToBigBed 

# Needed for tests that run with non-root user
RUN chmod -R a+rwx /opt/conda/envs/segtools-signal-distribution/

# It was a pain to try to get the conda-installed bigWigToBedGraph to work. Instead we
# add the binary ourselves, and mask the conda installed binary. The conda resolver
# didn't like me trying to upgrade the ucsc-bigwigtobedgraph to 377, got conflicts.
# Possibly related: https://github.com/bioconda/bioconda-recipes/issues/14724
COPY bin/* /utils/
COPY segway_pipeline/* /software/

ENV PATH=/utils:/software:$PATH
