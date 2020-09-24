version 1.0

import "../../../segway.wdl" as segway

workflow test_make_genomedata {
    input {
        Array[File] bigwigs
        File chrom_sizes
        Array[String] tracks
    }

    call segway.make_genomedata { input:
        bigwigs = bigwigs,
        chrom_sizes = chrom_sizes,
        tracks = tracks,
    }
}
