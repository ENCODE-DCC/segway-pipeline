from pathlib import Path

import pytest


@pytest.mark.workflow("test_segway_reinterpretation")
def test_segway_reinterpretation_relabeled_bed_files_match(
    workflow_dir, skip_n_lines_md5
):
    bed_path = workflow_dir / Path("test-output/relabeled.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "ce5428650eb6d345f21f4dd76ac63858"


@pytest.mark.workflow("test_segway_reinterpretation")
def test_segway_reinterpretation_recolored_bed_files_match(
    workflow_dir, skip_n_lines_md5
):
    bed_path = workflow_dir / Path("test-output/recolored.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "3e126751db7b980a6ff2e399d7930ca9"
