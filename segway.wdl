version 1.0

workflow segway {
    meta {
        version: "0.1.0"
        caper_docker: "encodedcc/hic-pipeline:0.1.0"
        caper_singularity: "docker://encodedcc/hic-pipeline:0.1.0"
    }

    input {
        # Pipeline inputs to run from beginning
        Array[File]? bigwigs
        Array[String]? assays
        File? chrom_sizes
        File annotation_gtf
        File model_pickle

        # Segway resource parameter
        Int num_segway_cpus = 96

        # Segway training hyperparameters. First three defaults taken from Libbrecht et al 2019
        Int resolution = 100
        Float minibatch_fraction = 0.01
        Int max_train_rounds = 25
        Int num_instances = 10
        Float prior_strength = 1.0
        Float segtransition_weight_scale = 1.0
        Int ruler_scale = 100

        # Segtools parameters
        Int segtools_aggregation_flank_bases = 10000

        # Optional inputs for starting the pipeline not from the beginning
        File? genomedata
        Int? num_labels
        Int? num_tracks
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
            resolution = resolution,
            prior_strength = prior_strength,
            segtransition_weight_scale = segtransition_weight_scale,
            ruler_scale = ruler_scale,
            track_weight = 1.0 / (100.0 * select_first([num_tracks, make_genomedata.num_tracks])),
            minibatch_fraction = minibatch_fraction,
            max_train_rounds = max_train_rounds,
            num_instances = num_instances,
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
        genomedata = select_first([genomedata, make_genomedata.genomedata]),
        segway_output_bed = segway_output_bed_,
        annotation_gtf = annotation_gtf,
        segway_params = segway_params_,
        flank_bases = segtools_aggregation_flank_bases,
    }

    if (defined(bigwigs) && defined(assays)) {
        call make_trackname_assay { input:
            tracknames = select_first([bigwigs]),
            assays = select_first([assays]),
        }

        call interpretation { input:
            trackname_assay = make_trackname_assay.trackname_assay,
            model_pickle = model_pickle,
            feature_aggregation_tab = segtools.feature_aggregation_tab,
            signal_distribution_tab = segtools.signal_distribution_tab,
            segment_sizes_tab = segtools.segment_sizes_tab,
            length_distribution_tab = segtools.length_distribution_tab
        }

        call relabel { input:
            bed = segway_output_bed_,
            mnemonics = interpretation.mnemonics,
        }

        call recolor_bed { input:
            bed = relabel.relabeled_bed
        }

        if (defined(chrom_sizes)) {
            call bed_to_bigbed as recolored_bed_to_bigbed { input:
                bed = recolor_bed.recolored_bed,
                chrom_sizes = select_first([chrom_sizes]),
                output_stem = "recolored",
            }
        }
    }
}

task make_genomedata {
    input {
        Array[File] bigwigs
        File chrom_sizes
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
    }
}

task segway_annotate {
    input {
        File genomedata
        File traindir
        Int ncpus
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
        gzip -nc segway.bed > segway.bed.gz
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
        File bed
        File chrom_sizes
        String output_stem = "recolored"
    }

    command <<<
        set -euo pipefail
        gzip -dc ~{bed} | tail -n +2 > ~{output_stem}.bed
        bedToBigBed ~{output_stem}.bed ~{chrom_sizes} ~{output_stem}.bb
        gzip -n ~{output_stem}.bed
    >>>

    output {
        File bigbed = "~{output_stem}.bb"
        File bed_no_header = "~{output_stem}.bed.gz"
    }
}

task segtools {
    input {
        File genomedata
        File segway_output_bed
        File annotation_gtf
        File segway_params
        Int flank_bases
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
    }
}

task make_trackname_assay {
    input {
        Array[String] tracknames
        Array[String] assays
        String output_filename = "trackname_assay.txt"
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
    }
}


task interpretation {
    input {
        File model_pickle
        File feature_aggregation_tab
        File signal_distribution_tab
        File trackname_assay
        File segment_sizes_tab
        File length_distribution_tab
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
            --model-path ~{model_pickle} \
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
    }
}


task relabel {
    input {
        File bed
        File mnemonics
        String output_stem = "relabeled"
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
    }
}

task recolor_bed {
    input {
        File bed
        String output_filename = "recolored.bed"
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
    }
}
