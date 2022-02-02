version 1.0

import "../../../segway.wdl" as segway

workflow test_relabel {
    input {
        File bed
        File mnemonics
        RuntimeEnvironment runtime_environment
    }

    call segway.relabel { input:
        bed = bed,
        mnemonics = mnemonics,
        runtime_environment = runtime_environment,
    }
}
