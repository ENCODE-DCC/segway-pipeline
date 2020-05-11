version 1.0

import "../../../segway.wdl" as segway

workflow test_segway_annotate {
    input {
        Array[File] bigwigs
        File annotation_gtf
        File chrom_sizes
        Float minibatch_fraction
        Float segtransition_weight_scale
        Float? prior_strength
        Int max_train_rounds
        Int ncpus
        Int num_instances
        Int num_labels
        Int resolution
    }

    call segway.segway { input:
        bigwigs = bigwigs,
        annotation_gtf = annotation_gtf,
        chrom_sizes = chrom_sizes,
        ncpus = ncpus,
        num_labels = num_labels,
        resolution = resolution,
        minibatch_fraction = minibatch_fraction,
        max_train_rounds = max_train_rounds,
        num_instances = num_instances,
        prior_strength = prior_strength,
        segtransition_weight_scale = segtransition_weight_scale,
    }
}
