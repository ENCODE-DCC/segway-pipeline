version 1.0

import "../../../segway.wdl" as segway

workflow test_relabel {
    input {
        File bed
        File mnemonics
    }

    call segway.relabel { input:
        bed = bed,
        mnemonics = mnemonics,
    }
}
