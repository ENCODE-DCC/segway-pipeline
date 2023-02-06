version 1.0

struct RuntimeEnvironment {
    String docker
    String singularity
}

workflow segway {
    meta {
        version: "1.2.0"
        caper_docker: "encodedcc/segway-pipeline:1.2.0"
        caper_singularity: "docker://encodedcc/segway-pipeline:1.2.0"
        description: "ENCODE Segway pipeline, see https://github.com/ENCODE-DCC/segway-pipeline for details."
    }

    input {
        # Pipeline inputs to run from beginning
        Array[File]? bigwigs
        Array[String] assays
        File chrom_sizes
        File annotation_gtf

        # Segway resource parameter
        Int num_segway_cpus = 96

        # Segway training hyperparameters. First three defaults taken from Libbrecht et al 2019
        Int resolution = 100
        Float minibatch_fraction = 0.01
        Int max_train_rounds = 25
        Int num_instances = 10
        Int? num_labels
        Float prior_strength = 1.0
        Float segtransition_weight_scale = 1.0
        Float track_weight = 0.01
        Int ruler_scale = 100

        # Segtools parameters
        Int segtools_aggregation_flank_bases = 10000

        # Optional inputs for reinterpretation
        File? segway_output_bed
        Array[String]? tracknames
        File? feature_aggregation_tab
        File? signal_distribution_tab
        File? segment_sizes_tab
        File? length_distribution_tab

        String docker = "encodedcc/segway-pipeline:1.2.0"
        String singularity = "docker://encodedcc/segway-pipeline:1.2.0"
    }

    RuntimeEnvironment runtime_environment = {
      "docker": docker,
      "singularity": singularity
    }

    if (!defined(segway_output_bed)) {
        call make_genomedata { input:
            bigwigs = select_all([bigwigs])[0],
            chrom_sizes = chrom_sizes,
            runtime_environment = runtime_environment,
        }

        call segway_train { input:
            genomedata = make_genomedata.genomedata,
            num_labels = select_first([num_labels, make_genomedata.num_labels]),
            resolution = resolution,
            prior_strength = prior_strength,
            segtransition_weight_scale = segtransition_weight_scale,
            ruler_scale = ruler_scale,
            track_weight = track_weight,
            minibatch_fraction = minibatch_fraction,
            max_train_rounds = max_train_rounds,
            num_instances = num_instances,
            ncpus = num_segway_cpus,
            runtime_environment = runtime_environment,
        }

        call segway_annotate { input:
            genomedata = make_genomedata.genomedata,
            traindir = segway_train.traindir,
            ncpus = num_segway_cpus,
            runtime_environment = runtime_environment,
        }

        call segtools { input:
            genomedata = make_genomedata.genomedata,
            segway_output_bed = segway_annotate.output_bed,
            annotation_gtf = annotation_gtf,
            segway_params = segway_annotate.segway_params,
            flank_bases = segtools_aggregation_flank_bases,
            runtime_environment = runtime_environment,
        }

        call make_trackname_assay { input:
            tracknames = select_first([bigwigs]),
            assays = assays,
            runtime_environment = runtime_environment,
        }

        call interpretation { input:
            trackname_assay = make_trackname_assay.trackname_assay,
            feature_aggregation_tab = segtools.feature_aggregation_tab,
            signal_distribution_tab = segtools.signal_distribution_tab,
            segment_sizes_tab = segtools.segment_sizes_tab,
            length_distribution_tab = segtools.length_distribution_tab,
            runtime_environment = runtime_environment,
        }
    }

    if (defined(segway_output_bed)) {
        call make_trackname_assay as make_trackname_assay_from_strings { input:
            tracknames = select_first([tracknames]),
            assays = assays,
            runtime_environment = runtime_environment,
        }

        call interpretation as interpret_existing_bed { input:
            trackname_assay = make_trackname_assay_from_strings.trackname_assay,
            feature_aggregation_tab = select_first([feature_aggregation_tab]),
            signal_distribution_tab = select_first([signal_distribution_tab]),
            segment_sizes_tab = select_first([segment_sizes_tab]),
            length_distribution_tab = select_first([length_distribution_tab]),
            runtime_environment = runtime_environment,
        }
    }

    File segway_output_bed_ = select_first([segway_output_bed, segway_annotate.output_bed])
    File mnemonics = select_first([interpretation.mnemonics, interpret_existing_bed.mnemonics])

    call relabel { input:
        bed = segway_output_bed_,
        mnemonics = mnemonics,
        runtime_environment = runtime_environment,
    }

    call recolor_bed { input:
        bed = relabel.relabeled_bed,
        runtime_environment = runtime_environment,
    }

    if (defined(chrom_sizes)) {
        call bed_to_bigbed as recolored_bed_to_bigbed { input:
            bed = recolor_bed.recolored_bed,
            chrom_sizes = chrom_sizes,
            output_stem = "recolored",
            runtime_environment = runtime_environment,
        }
    }
}

task make_genomedata {
    input {
        Array[File] bigwigs
        File chrom_sizes
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
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
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}

task segway_train {
    input {
        File genomedata
        Int num_labels
        Int resolution
        Float prior_strength
        Float segtransition_weight_scale
        Int ruler_scale
        Float track_weight
        Float minibatch_fraction
        Int max_train_rounds
        Int num_instances
        Int ncpus
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
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
            --prior-strength ~{prior_strength} \
            --segtransition-weight-scale ~{segtransition_weight_scale} \
            --ruler-scale ~{ruler_scale} \
            --track-weight ~{track_weight} \
            --max-train-rounds ~{max_train_rounds} \
            ~{genomedata} \
            traindir
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
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}

task segway_annotate {
    input {
        File genomedata
        File traindir
        Int ncpus
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
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
        tail -n +2 segway.bed > segway_no_header.bed
        gzip -nc segway_no_header.bed > segway.bed.gz
        find identifydir -print0 |
            LC_ALL=C sort -z |
            tar --owner=0 --group=0 --numeric-owner --mtime='2019-01-01 00:00Z' \
            --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
            --no-recursion --null -T - -cf identifydir.tar
        gzip -nc identifydir.tar > identifydir.tar.gz
    >>>

    output {
        File segway_params = "training_params.tar.gz"
        File identifydir = "identifydir.tar.gz"
        File output_bed = "segway.bed.gz"
    }

    runtime {
        cpu: ncpus
        memory: "400 GB"
        disks: "local-disk 1000 SSD"
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}

task bed_to_bigbed {
    input {
        File bed
        File chrom_sizes
        String output_stem = "segway"
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
        gzip -dc ~{bed} > ~{output_stem}.bed
        bedToBigBed ~{output_stem}.bed ~{chrom_sizes} ~{output_stem}.bb
        gzip -n ~{output_stem}.bed
    >>>

    output {
        File bigbed = "~{output_stem}.bb"
    }

    runtime {
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}

task segtools {
    input {
        File genomedata
        File segway_output_bed
        File annotation_gtf
        File segway_params
        Int flank_bases
        RuntimeEnvironment runtime_environment
    }

    command <<<
        # Can't set the usual values since some of the commands fail with nonzero
        # set -euo pipefail
        mkdir segway_params && tar xf ~{segway_params} -C segway_params --strip-components 1
        segtools-length-distribution -o length_distribution ~{segway_output_bed}
        segtools-gmtk-parameters  -o gmtk_parameters segway_params/params/params.params
        segtools-aggregation \
            --normalize \
            -o feature_aggregation \
            --mode=gene \
            --flank-bases=~{flank_bases} \
            ~{segway_output_bed} \
            ~{annotation_gtf}
        # TODO: undo temporary env fix once segtools is patched. Use conda run to avoid bashrc wackiness
        conda run -n segtools-signal-distribution \
            segtools-signal-distribution \
                --transformation arcsinh \
                -o signal_distribution \
                ~{segway_output_bed} \
                ~{genomedata} \
            || true
    >>>

    output {
        Array[File] length_distribution_info = glob("length_distribution/*")
        File length_distribution_tab = "length_distribution/length_distribution.tab"
        File segment_sizes_tab = "length_distribution/segment_sizes.tab"
        Array[File] gmtk_info = glob("gmtk_parameters/*")
        Array[File] feature_aggregation_info = glob("feature_aggregation/*")
        File feature_aggregation_tab = "feature_aggregation/feature_aggregation.tab"
        Array[File] signal_distribution_info = glob("signal_distribution/*")
        File signal_distribution_tab = "signal_distribution/signal_distribution.tab"
    }

    runtime {
        cpu: 8
        memory: "16 GB"
        disks: "local-disk 250 SSD"
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}

task make_trackname_assay {
    input {
        Array[String] tracknames
        Array[String] assays
        String output_filename = "trackname_assay.txt"
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
        python \
            "$(which make_trackname_assay.py)" \
            --tracknames ~{sep=" " tracknames} \
            --assays ~{sep=" " assays} \
            --output-filename ~{output_filename}
    >>>

    output {
        File trackname_assay = "~{output_filename}"
    }

    runtime {
        cpu: 1
        memory: "2 GB"
        disks: "local-disk 10 SSD"
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}


task interpretation {
    input {
        File feature_aggregation_tab
        File signal_distribution_tab
        File trackname_assay
        File segment_sizes_tab
        File length_distribution_tab
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
        export SEGWAY_OUTPUT=segwayOutput
        export SAMPLE_NAME=sample
        mkdir -p "${SEGWAY_OUTPUT}/${SAMPLE_NAME}/"
        mv ~{trackname_assay} "${SEGWAY_OUTPUT}"
        mv \
            ~{feature_aggregation_tab} \
            ~{signal_distribution_tab} \
            ~{segment_sizes_tab} \
            ~{length_distribution_tab} \
            "${SEGWAY_OUTPUT}/${SAMPLE_NAME}"
        python \
            "$(which apply_samples.py)" \
            interpretation-output \
            --model-path /opt/interpretation_samples/model_300_reg.020_auc0.89V04.pickle.gz \
            --input-path "${PWD}/${SEGWAY_OUTPUT}"
    >>>

    output {
        Array[File] stats = glob("interpretation-output/stats/*")
        File mnemonics = "interpretation-output/classification/sample/mnemonics.txt"
        File classifier_data = "interpretation-output/classification/sample/classifier_data.tab"
        File classifier_probailities = "interpretation-output/classification/sample/probs.txt"
    }

    runtime {
        cpu: 4
        memory: "16 GB"
        disks: "local-disk 100 SSD"
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}


task relabel {
    input {
        File bed
        File mnemonics
        String output_stem = "relabeled"
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
        gzip -dc ~{bed} > decompressed.bed
        python \
            "$(which relabel.py)" \
            -o ~{output_stem}.bed \
            decompressed.bed \
            ~{mnemonics}
        gzip -n ~{output_stem}.bed
    >>>

    output {
        File relabeled_bed = "~{output_stem}.bed.gz"
    }

    runtime {
        cpu: 1
        memory: "2 GB"
        disks: "local-disk 20 SSD"
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}

task recolor_bed {
    input {
        File bed
        String output_filename = "recolored.bed"
        RuntimeEnvironment runtime_environment
    }

    command <<<
        set -euo pipefail
        gzip -dc ~{bed} > decompressed.bed
        python "$(which recolor_bed.py)" -o ~{output_filename} decompressed.bed
        gzip -n ~{output_filename}
    >>>

    output {
        File recolored_bed = "~{output_filename}.gz"
    }

    runtime {
        cpu: 1
        memory: "2 GB"
        disks: "local-disk 20 SSD"
        docker: runtime_environment.docker
        singularity: runtime_environment.singularity
    }
}
