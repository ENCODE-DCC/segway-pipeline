version 1.0

#CAPER docker encodedcc/segway-pipeline:0.1.0
#CAPER singularity docker://encodedcc/segway-pipeline:0.1.0

workflow segway {
    input {
        # Pipeline inputs to run from beginning
        Array[File]? bigwigs
        File? chrom_sizes
        File annotation_gtf

        # Segway resource parameter
        Int num_segway_cpus = 96

        # Segway training hyperparameters. First three defaults taken from Libbrecht et al 2019
        Int resolution = 100
        Float minibatch_fraction = 0.01
        Int max_train_rounds = 25
        Int num_instances = 10
        Float prior_strength = 1
        Float? segtransition_weight_scale

        # Optional inputs for starting the pipeline not from the beginning
        File? genomedata
        Int? num_labels
        File? segway_traindir
        File? segway_output_bed
        File? segway_params
    }

    Boolean has_make_genomedata_input = defined(bigwigs) && defined(chrom_sizes)
    Boolean has_segtools_input = defined(segway_output_bed) && defined(segway_params) && defined(genomedata)
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
            num_labels = select_first([num_labels, make_genomedata.num_labels]),
            ncpus = num_segway_cpus,
            resolution = resolution,
            minibatch_fraction = minibatch_fraction,
            max_train_rounds = max_train_rounds,
            num_instances = num_instances,
            # specifying prior strength causes segway to crash:
            # https://bitbucket.org/hoffmanlab/segway/issues/136/using-the-prior-strength-option-causes
            # prior_strength = prior_strength,
            segtransition_weight_scale = select_first([make_genomedata.num_tracks, segtransition_weight_scale])
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

    Boolean has_segway_output_bed = defined(segway_output_bed)

    if (has_segway_output_bed && defined(chrom_sizes)) {
        call bed_to_bigbed { input:
            segway_output_bed = segway_output_bed_,
            chrom_sizes = select_all([chrom_sizes])[0],
        }
    }


    call segtools { input:
        genomedata = select_first([genomedata, make_genomedata.genomedata]),
        segway_output_bed = segway_output_bed_,
        annotation_gtf = annotation_gtf,
        segway_params = segway_params_,
    }
}

task make_genomedata {
    input {
        Array[File] bigwigs
        File chrom_sizes
    }

    command <<<
        python "$(which make_genomedata.py)" --files ~{sep=" " bigwigs} --sizes ~{chrom_sizes} -o files.genomedata
        python "$(which calculate_num_labels.py)" --num-tracks ~{length(bigwigs)} -o num_labels.txt
    >>>

    output {
        File genomedata = "files.genomedata"
        Int num_labels = read_int("num_labels.txt")
        Int num_tracks = length(bigwigs)
    }

    runtime {
        cpu: 4
        memory: "16 GB"
        disks: "local-disk 500 SSD"
    }
}

task segway_train {
    input {
        File genomedata
        Int num_labels
        Int ncpus
        Int resolution
        Float minibatch_fraction
        Int max_train_rounds
        Int num_instances
        Float? prior_strength
        Float segtransition_weight_scale
    }

    command <<<
        mkdir tmp
        export TMPDIR="${PWD}/tmp"
        export SEGWAY_RAND_SEED=112344321
        export SEGWAY_NUM_LOCAL_JOBS=~{ncpus}
        export OMP_NUM_THREADS=1
        mkdir traindir
        SEGWAY_CLUSTER=local segway train \
            --num-labels ~{num_labels} \
            --resolution ~{resolution} \
            --minibatch-fraction ~{minibatch_fraction} \
            --num-instances ~{num_instances} \
            ~{if defined(prior_strength) then "--prior_strength " + prior_strength else ""} \
            --segtransition-weight-scale ~{segtransition_weight_scale} \
            --max-train-rounds ~{max_train_rounds} \
            ~{genomedata} traindir
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
        File traindir = "traindir.tar.gz"
        # Checks that the model training actually emitted final params, not used
        File trained_params = "traindir/params/params.params"
    }

    runtime {
        cpu: ncpus
        memory: "300 GB"
        disks: "local-disk 1000 SSD"
    }
}

task segway_annotate {
    input {
        File genomedata
        File traindir
        Int ncpus
    }

    command <<<
        mkdir tmp
        export TMPDIR="${PWD}/tmp"
        export SEGWAY_RAND_SEED=112344321
        export SEGWAY_NUM_LOCAL_JOBS=~{ncpus}
        export OMP_NUM_THREADS=1
        mkdir traindir && tar xf ~{traindir} -C traindir --strip-components 1
        mkdir identifydir
        SEGWAY_CLUSTER=local segway annotate ~{genomedata} --bed=segway.bed traindir identifydir
        find traindir -regextype egrep -regex 'traindir/(auxiliary|params/input.master|params/params.params|segway.str|triangulation)($|/.*)' -print0 |
            LC_ALL=C sort -z |
            tar --owner=0 --group=0 --numeric-owner --mtime='2019-01-01 00:00Z' \
            --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
            --no-recursion --null -T - -cf training_params.tar
        gzip -nc training_params.tar > training_params.tar.gz
        gzip -nc segway.bed > segway.bed.gz
    >>>

    output {
        File segway_params = "training_params.tar.gz"
        File output_bed = "segway.bed.gz"
        Array[File] logs = glob("identifydir/output/e/identify/*")
    }

    runtime {
        cpu: ncpus
        memory: "400 GB"
        disks: "local-disk 1000 SSD"
    }
}

task bed_to_bigbed {
    input {
        File segway_output_bed
        File chrom_sizes
    }

    command <<<
        set -euo pipefail
        gzip -dc ~{segway_output_bed} > segway.bed
        bedToBigBed segway.bed ~{chrom_sizes} segway.bb

        # without this sleep command, bedToBigBed command in above line fails.
        # sleep 2

    >>>

    output {
        File output_big_bed = "segway.bb"
    }

}


task segtools {
    input {
        File genomedata
        File segway_output_bed
        File annotation_gtf
        File segway_params
    }

    command <<<
        mkdir segway_params && tar xf ~{segway_params} -C segway_params --strip-components 1
        segtools-length-distribution -o length_distribution ~{segway_output_bed}
        segtools-gmtk-parameters  -o gmtk_parameters segway_params/params/params.params
        segtools-aggregation --normalize -o feature_aggregation --mode=gene ~{segway_output_bed} ~{annotation_gtf}
        # TODO: undo temporary env fix once segtools is patched. Use conda run to avoid bashrc wackiness
        conda run -n segtools-signal-distribution \
            segtools-signal-distribution \
                --transformation arcsinh \
                -o signal_distribution \
                ~{segway_output_bed} \
                ~{genomedata}
    >>>

    output {
        Array[File] length_distribution_info = glob("length_distribution/*")
        Array[File] gmtk_info = glob("gmtk_parameters/*")
        Array[File] feature_aggregation_info = glob("feature_aggregation/*")
        Array[File] signal_distribution_info = glob("signal_distribution/*")
    }

    runtime {
        cpu: 8
        memory: "16 GB"
        disks: "local-disk 250 SSD"
    }
}
