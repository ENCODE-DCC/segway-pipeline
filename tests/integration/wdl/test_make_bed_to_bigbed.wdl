version 1.0

import "../../../segway.wdl" as segway

workflow test_make_bed_to_bigbed    {
    input   {
        File output_bed
        File chrom_sizes
    }

    call segway.make_bed_to_bigbed { input: 
        output_bed = output_bed,
        chrom_sizes = chrom_sizes,
    }
}
