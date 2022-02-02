version 1.0

import "../../../segway.wdl" as segway

workflow test_bed_to_bigbed {
    input {
        File bed
        File chrom_sizes
        String output_stem
        RuntimeEnvironment runtime_environment
    }

    call segway.bed_to_bigbed { input:
        bed = bed,
        chrom_sizes = chrom_sizes,
        output_stem = output_stem,
        runtime_environment = runtime_environment,
    }
}
