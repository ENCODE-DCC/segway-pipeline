#CAPER docker quay.io/encode-dcc/segway:0.1.0
#CAPER singularity docker://quay.io/encode-dcc/segway:0.1.0

workflow segway {
    Array[File] bigwigs
    File chrom_sizes

    call make_genomedata { input:
        bigwigs = bigwigs,
        chrom_sizes = chrom_sizes
    }

    call segway_train_annotate { input:
        genomedata = make_genomedata.genomedata
    }
}

task make_genomedata {
    Array[File] bigwigs
    File chrom_sizes

    command {
        python "$(which make_genomedata.py)" --files ${sep=" " bigwigs} --sizes ${chrom_sizes}
    }

    output {
        File genomedata = glob("files.genomedata")[0]
    }

    runtime {
        cpu: 8
        memory: "16 GB"
        disks: "local-disk 500 SSD"
    }
}

task segway_train_annotate {
    File genomedata

    command {
        mkdir traindir identifydir
        segway train "${genomedata}" traindir
        segway annotate "${genomedata}" traindir identifydir
    }

    output {
        File metadata_csv = glob("gembs_metadata.csv")[0]
        File gembs_conf = glob("gembs.conf")[0]
    }

    runtime {
        cpu: 8
        memory: "16 GB"
        disks: "local-disk 500 SSD"
    }
}
