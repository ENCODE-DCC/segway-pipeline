from pathlib import Path

import pytest


@pytest.mark.workflow("test_make_genomedata")
def test_make_genomedata_hdf5_files_match(
    test_data_dir, workflow_dir, genomedatas_match
):
    actual_genomedata_path = workflow_dir / Path("test-output/files.genomedata")
    expected_genomedata_path = test_data_dir / Path("files.genomedata")
    assert genomedatas_match(actual_genomedata_path, expected_genomedata_path)
