version 1.0

import "../../../segway.wdl" as segway

workflow test_recolor_bed {
    input {
        File bed
    }

    call segway.recolor_bed { input:
        bed = bed,
    }
}
