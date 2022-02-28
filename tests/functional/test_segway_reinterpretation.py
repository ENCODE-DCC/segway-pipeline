from pathlib import Path

import pytest


@pytest.mark.workflow("test_segway_reinterpretation")
def test_segway_reinterpretation_relabeled_bed_files_match(
    workflow_dir, skip_n_lines_md5
):
    bed_path = workflow_dir / Path("test-output/relabeled.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "918ee533bcf51e318f6f4e586a8986dd"


@pytest.mark.workflow("test_segway_reinterpretation")
def test_segway_reinterpretation_recolored_bed_files_match(
    workflow_dir, skip_n_lines_md5
):
    bed_path = workflow_dir / Path("test-output/recolored.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "9b0936e73d4be7ff76fbfb5d54866e99"
