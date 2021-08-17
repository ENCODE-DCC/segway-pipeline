from pathlib import Path

import pytest


@pytest.mark.workflow("test_segway_train")
def test_segway_train_traindirs_match(test_data_dir, workflow_dir, traindirs_match):
    actual_traindir_path = workflow_dir / Path("test-output/traindir.tar.gz")
    expected_traindir_path = test_data_dir / Path("segway_train_traindir.tar.gz")
    assert traindirs_match(actual_traindir_path, expected_traindir_path, workflow_dir)
