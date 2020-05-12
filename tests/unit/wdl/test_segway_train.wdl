version 1.0

import "../../../segway.wdl" as segway

workflow test_segway_train {
    input {
        File genomedata
        Int max_train_rounds
        Float minibatch_fraction
        Int ncpus
        Int num_instances
        Int num_labels
        Float? prior_strength
        Int resolution
        Float segtransition_weight_scale
    }

    call segway.segway_train { input:
        genomedata = genomedata,
        num_labels = num_labels,
        ncpus = ncpus,
        resolution = resolution,
        minibatch_fraction = minibatch_fraction,
        max_train_rounds = max_train_rounds,
        num_instances = num_instances,
        prior_strength = prior_strength,
        segtransition_weight_scale = segtransition_weight_scale,
    }
}
