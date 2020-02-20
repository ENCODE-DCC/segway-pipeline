#CAPER docker quay.io/encode-dcc/segway@sha256:9da51e6bcfd2e95f91c9c5d420c57d0e1b2828f3de7d060e070d450459cd3797
#CAPER singularity docker://quay.io/encode-dcc/segway@sha256:9da51e6bcfd2e95f91c9c5d420c57d0e1b2828f3de7d060e070d450459cd3797

workflow segway {
    # Pipeline inputs to run from beginning
    Array[File]? bigwigs
    File? chrom_sizes
    File annotation_gtf

    # Pipeline resource parameter
    Int num_segway_cpus = 96

    # Optional inputs for starting the pipeline not from the beginning
    File? genomedata
    File? segway_traindir
    File? segway_output_bed
    File? segway_params

    Boolean has_make_genomedata_input = defined(bigwigs) && defined(chrom_sizes)
    Boolean has_segtools_input = defined(segway_output_bed) && defined(segway_params)
    # We need a genomedata for everything except segtools
    if (!defined(genomedata) && !has_segtools_input && has_make_genomedata_input) {
        call make_genomedata { input:
            bigwigs = select_all([bigwigs])[0],
            chrom_sizes = select_all([chrom_sizes])[0],
        }
    }

    # We can skip training if we have a traindir or if we just need to run segtools
    if (!defined(segway_traindir) && !has_segtools_input) {
        call segway_train { input:
            genomedata = select_first([genomedata, make_genomedata.genomedata]),
            ncpus = num_segway_cpus,
        }
    }

    if (!has_segtools_input) {
        call segway_annotate { input:
            genomedata = select_first([genomedata, make_genomedata.genomedata]),
            traindir = select_first([segway_traindir, segway_train.traindir]),
            ncpus = num_segway_cpus,
        }
    }

    File segway_output_bed_ = select_first([segway_output_bed, segway_annotate.output_bed])
    File segway_params_ = select_first([segway_params, segway_annotate.segway_params])

    call segtools { input:
        segway_output_bed = segway_output_bed_,
        annotation_gtf = annotation_gtf,
        segway_params = segway_params_,
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

task segway_train {
    File genomedata
    Int ncpus

    command <<<
        export SEGWAY_RAND_SEED=112344321
        export SEGWAY_NUM_LOCAL_JOBS=${ncpus}
        mkdir traindir
        segway train ${genomedata} traindir
        # See https://stackoverflow.com/a/54908072 and
        # https://reproducible-builds.org/docs/archives/. Want to make tar idempotent
        find traindir -print0 |
            LC_ALL=C sort -z |
            tar --owner=0 --group=0 --numeric-owner --mtime='2019-01-01 00:00Z' \
            --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
            --no-recursion --null -T - -cf traindir.tar
        gzip -nc traindir.tar > traindir.tar.gz
    >>>

    output {
        File traindir = glob("traindir.tar.gz")[0]
    }

    runtime {
        cpu: ncpus
        memory: "32 GB"
        disks: "local-disk 500 SSD"
    }
}

task segway_annotate {
    File genomedata
    File traindir
    Int ncpus

    command {
        mkdir tmp
        export TMPDIR="$PWD/tmp"
        export SEGWAY_RAND_SEED=112344321
        export SEGWAY_NUM_LOCAL_JOBS=${ncpus}
        mkdir traindir && tar xf ${traindir} -C traindir --strip-components 1
        mkdir identifydir
        segway annotate ${genomedata} --bed=segway.bed.gz traindir identifydir
        find traindir -regextype egrep -regex 'traindir/(auxiliary|params/input.master|params/params.params|segway.str|triangulation)($|/.*)' -print0 |
            LC_ALL=C sort -z |
            tar --owner=0 --group=0 --numeric-owner --mtime='2019-01-01 00:00Z' \
            --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
            --no-recursion --null -T - -cf training_params.tar
        gzip -nc training_params.tar > training_params.tar.gz
}

    output {
        File segway_params = glob("training_params.tar.gz")[0]
        File output_bed = glob("segway.bed.gz")[0]
    }

    runtime {
        cpu: ncpus
        memory: "200 GB"
        disks: "local-disk 500 SSD"
    }
}

task segtools {
    File segway_output_bed
    File annotation_gtf
    File segway_params

    command {
        mkdir segway_params && tar xf ${segway_params} -C segway_params --strip-components 1
        segtools-length-distribution -o length_distribution ${segway_output_bed}
        segtools-gmtk-parameters  -o gmtk_parameters segway_params/params/params.params
        segtools-aggregation --normalize -o feature_aggregation --mode=gene ${segway_output_bed} ${annotation_gtf}
        # TODO: add SAGA interpretation
    }

    output {
        Array[File] length_distribution_info = glob("length_distribution/*")
        Array[File] gmtk_info = glob("gmtk_parameters/*")
        Array[File] feature_aggregation_info = glob("feature_aggregation/*")
    }

    runtime {
        cpu: 8
        memory: "16 GB"
        disks: "local-disk 250 SSD"
    }
}
