version 1.0

import "../../../segway.wdl" as segway

workflow test_segway_annotate {
    input {
        File genomedata
        File traindir
        Int ncpus
        RuntimeEnvironment runtime_environment
    }

    call segway.segway_annotate { input:
        genomedata = genomedata,
        traindir = traindir,
        ncpus = ncpus,
        runtime_environment = runtime_environment,
    }
}
