#CAPER docker quay.io/encode-dcc/segway@sha256:d61b57fc6790f57af784c9e3ad1129b5cf9b3fb458e166d8ed54242734fb6b8e
#CAPER singularity docker://quay.io/encode-dcc/segway:@sha256:d61b57fc6790f57af784c9e3ad1129b5cf9b3fb458e166d8ed54242734fb6b8e

workflow segway {
    Array[File] bigwigs
    File chrom_sizes
    File annotation_gff

    call make_genomedata { input:
        bigwigs = bigwigs,
        chrom_sizes = chrom_sizes
    }

    call segway_train_annotate { input:
        genomedata = make_genomedata.genomedata
    }

    call segtools { input:
        segway_output_bed = segway_train_annotate.output_bed,
        annotation_gff = annotation_gff,
        segway_params = segway_train_annotate.model_params
    }
}

task make_genomedata {
    Array[File] bigwigs
    File chrom_sizes

    command {
        python "$(which make_genomedata.py)" --files ${sep=" " bigwigs} --sizes ${chrom_sizes} -o files.genomedata
    }

    output {
        File genomedata = glob("files.genomedata")[0]
    }

    runtime {
        cpu: 4
        memory: "16 GB"
        disks: "local-disk 500 SSD"
    }
}

task segway_train_annotate {
    File genomedata

    command {
        export SEGWAY_RAND_SEED=112344321
        mkdir traindir identifydir
        segway train "${genomedata}" traindir
        segway annotate "${genomedata}" --bed=segway.bed.gz traindir identifydir
    }

    output {
        File model_params = glob("traindir/params.params")[0]
        File output_bed = glob("segway.bed.gz")[0]
    }

    runtime {
        cpu: 8
        memory: "16 GB"
        disks: "local-disk 500 SSD"
    }
}

task segtools {
    File segway_output_bed
    File annotation_gff
    File segway_params

    command {
        segtools-length-distribution -o length_distribution ${segway_output_bed}
        segtools-gmtk-parameters  -o gmtk_parameters ${segway_params}
        segtools-aggregation --normalize -o feature_aggregation --mode region ${segway_output_bed} ${annotation_gff}
        # TODO: add Tony's automated classification
    }

    output {
        Array[File] length_distribution_info = glob("length_distribution/*")
        Array[File] gmtk_info = glob("gmtk_parameters/*")
        Array[File] feature_aggregation_info = glob("feature_aggregation/*")
    }
}
