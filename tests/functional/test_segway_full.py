from pathlib import Path

import pytest


@pytest.mark.workflow("test_segway_full")
def test_segway_train_traindirs_match(test_data_dir, workflow_dir, traindirs_match):
    actual_traindir_path = workflow_dir / Path("test-output/traindir.tar.gz")
    expected_traindir_path = test_data_dir / Path("segway_full_traindir.tar.gz")
    assert traindirs_match(actual_traindir_path, expected_traindir_path, workflow_dir)


@pytest.mark.workflow("test_segway_full")
def test_segway_annotate_bed_files_match(test_data_dir, workflow_dir, skip_n_lines_md5):
    bed_path = workflow_dir / Path("test-output/segway.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "023096ca150a0752e8bacc6c7c52019f"


@pytest.mark.workflow("test_segway_full")
def test_segway_full_relabeled_bed_files_match(workflow_dir, skip_n_lines_md5):
    bed_path = workflow_dir / Path("test-output/relabeled.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "dbbd3c7965685a2b28e04e4baa82471b"


@pytest.mark.workflow("test_segway_full")
def test_segway_full_recolored_bed_files_match(workflow_dir, skip_n_lines_md5):
    bed_path = workflow_dir / Path("test-output/recolored.bed.gz")
    md5sum = skip_n_lines_md5(bed_path, n_lines=0)
    assert md5sum == "9896aa48cf4a7b3164952ae797b4cff2"


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
