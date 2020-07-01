version 1.0

import "../../../segway.wdl" as segway

workflow test_make_bed_to_bigbed    {
    input   {
        File segway_output_bed
        File chrom_sizes
    }

    call segway.bed_to_bigbed { input:
        segway_output_bed = segway_output_bed,
        chrom_sizes = chrom_sizes,
    }
}
