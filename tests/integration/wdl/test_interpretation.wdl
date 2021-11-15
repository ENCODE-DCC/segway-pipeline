version 1.0

import "../../../segway.wdl" as segway

workflow test_interpretation {
    input {
        File feature_aggregation_tab
        File length_distribution_tab
        File segment_sizes_tab
        File signal_distribution_tab
        File trackname_assay
    }

    call segway.interpretation { input:
        feature_aggregation_tab = feature_aggregation_tab,
        length_distribution_tab = length_distribution_tab,
        segment_sizes_tab = segment_sizes_tab,
        signal_distribution_tab = signal_distribution_tab,
        trackname_assay = trackname_assay,
    }
}
