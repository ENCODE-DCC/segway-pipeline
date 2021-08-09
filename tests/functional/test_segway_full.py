from pathlib import Path

import pytest


@pytest.mark.workflow("test_segway_full")
def test_segway_train_traindirs_match(test_data_dir, workflow_dir, traindirs_match):
    actual_traindir_path = workflow_dir / Path(
        "test-output/traindir.tar.gz"
    )
    expected_traindir_path = test_data_dir / Path("segway_full_traindir.tar.gz")
    assert traindirs_match(actual_traindir_path, expected_traindir_path, workflow_dir)


@pytest.mark.workflow("test_segway_full")
def test_segway_annotate_bed_files_match(
    test_data_dir, workflow_dir, skip_n_lines_and_compare
):
    """
    Bed header contains nondeterministic workflow data, need to skip it when comparing.
    """
    actual_bed_path = workflow_dir / Path("test-output/segway.bed.gz")
    expected_bed_path = test_data_dir / Path("segway_full.bed.gz")
    assert skip_n_lines_and_compare(actual_bed_path, expected_bed_path, n_lines=1)


@pytest.mark.workflow("test_segway_full")
def test_segway_full_length_distribution_pdfs_match(
    workflow_dir, test_data_dir, pdfs_match
):
    result = workflow_dir / Path(
        "test-output/glob-a287da44f32bf6a3fc6d7c51c52ddafa/length_distribution.pdf"
    )
    expected = test_data_dir / Path("segway_full_length_distribution.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segway_full")
def test_segway_full_segment_sizes_pdfs_match(workflow_dir, test_data_dir, pdfs_match):
    result = workflow_dir / Path(
        "test-output/glob-a287da44f32bf6a3fc6d7c51c52ddafa/segment_sizes.pdf"
    )
    expected = test_data_dir / Path("segway_full_segment_sizes.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segway_full")
def test_segway_full_gmtk_parameters_pdfs_match(
    workflow_dir, test_data_dir, pdfs_match
):
    result = workflow_dir / Path(
        "test-output/glob-03b7332b8fdb9a1ca33a23093d5878d5/gmtk_parameters.pdf"
    )
    expected = test_data_dir / Path("segway_full_gmtk_parameters.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segway_full")
def test_segway_full_feature_aggregation_splicing_pdfs_match(
    workflow_dir, test_data_dir, pdfs_match
):
    result = workflow_dir / Path(
        "test-output/glob-9a503dc39dbe819d5ebf7343f90bb109/feature_aggregation.splicing.pdf"
    )
    expected = test_data_dir / Path("segway_full_feature_aggregation.splicing.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segway_full")
def test_segway_full_feature_aggregation_translation_pdfs_match(
    workflow_dir, test_data_dir, pdfs_match
):
    result = workflow_dir / Path(
        "test-output/glob-9a503dc39dbe819d5ebf7343f90bb109/feature_aggregation.translation.pdf"
    )
    expected = test_data_dir / Path("segway_full_feature_aggregation.translation.pdf")
    assert pdfs_match(result, expected)
