#CAPER docker quay.io/encode-dcc/segway@sha256:9da51e6bcfd2e95f91c9c5d420c57d0e1b2828f3de7d060e070d450459cd3797
#CAPER singularity docker://quay.io/encode-dcc/segway@sha256:9da51e6bcfd2e95f91c9c5d420c57d0e1b2828f3de7d060e070d450459cd3797

workflow segway {
    Array[File] bigwigs
    File chrom_sizes
    File annotation_gff
    Int num_segway_cpus = 96

    call make_genomedata { input:
        bigwigs = bigwigs,
        chrom_sizes = chrom_sizes
    }

    call segway_train_annotate { input:
        genomedata = make_genomedata.genomedata,
        ncpus = num_segway_cpus,
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
    Int ncpus

    command <<<
        export SEGWAY_RAND_SEED=112344321
        export SEGWAY_NUM_LOCAL_JOBS=${ncpus}
        mkdir traindir identifydir
        segway train ${genomedata} traindir
        segway annotate ${genomedata} --bed=segway.bed.gz traindir identifydir
        # See https://stackoverflow.com/a/54908072 . Want to make tar idempotent
        echo traindir/{auxiliary,params/input.master,params/params.params,segway.str,triangulation} |
            LC_ALL=C sort -z |
            tar --owner=0 --group=0 --numeric-owner --mtime='2019-01-01 00:00Z' \
            --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
            --no-recursion --null -T - -cf training_params.tar
        gzip -nc training_params.tar > training_params.tar.gz
    >>>

    output {
        File model_params = glob("traindir/params.params")[0]
        File output_bed = glob("segway.bed.gz")[0]
    }

    runtime {
        cpu: ncpus
        memory: "32 GB"
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
