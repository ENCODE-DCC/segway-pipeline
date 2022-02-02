version 1.0

import "../../../segway.wdl" as segway

workflow test_recolor_bed {
    input {
        File bed
        RuntimeEnvironment runtime_environment
    }

    call segway.recolor_bed { input:
        bed = bed,
        runtime_environment = runtime_environment,
    }
}
