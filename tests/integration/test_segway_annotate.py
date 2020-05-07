from pathlib import Path

import pytest


@pytest.mark.workflow(name="test_segway_annotate_integration")
def test_segway_annotate_bed_files_match(
    test_data_dir, workflow_dir, skip_n_lines_and_compare
):
    """
    Bed header contains nondeterministic workflow data, need to skip it when comparing.
    """
    actual_bed_path = workflow_dir / Path("test-output/segway.bed.gz")
    expected_bed_path = test_data_dir / Path("segway.bed.gz")
    assert skip_n_lines_and_compare(actual_bed_path, expected_bed_path, n_lines=1)
