version 1.0

import "../../../segway.wdl" as segway

workflow test_segtools {
    input {
        File genomedata
        File segway_output_bed
        File annotation_gtf
        File segway_params
    }

    call segway.segtools { input:
        genomedata = genomedata,
        segway_output_bed = segway_output_bed,
        annotation_gtf = annotation_gtf,
        segway_params = segway_params,
    }
}
