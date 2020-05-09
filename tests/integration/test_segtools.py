from pathlib import Path

import pytest


@pytest.mark.workflow("test_segtools_integration")
def test_segtools_length_distribution_pdfs_match(workflow_dir, test_data_dir, pdfs_match):
    result = workflow_dir / Path("test-output/glob-a287da44f32bf6a3fc6d7c51c52ddafa/length_distribution.pdf")
    expected = test_data_dir / Path("length_distribution.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segtools_integration")
def test_segtools_segment_sizes_pdfs_match(workflow_dir, test_data_dir, pdfs_match):
    result = workflow_dir / Path("test-output/glob-a287da44f32bf6a3fc6d7c51c52ddafa/segment_sizes.pdf")
    expected = test_data_dir / Path("segment_sizes.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segtools_integration")
def test_segtools_gmtk_parameters_pdfs_match(workflow_dir, test_data_dir, pdfs_match):
    result = workflow_dir / Path("test-output/glob-03b7332b8fdb9a1ca33a23093d5878d5/gmtk_parameters.pdf")
    expected = test_data_dir / Path("gmtk_parameters.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segtools_integration")
def test_segtools_feature_aggregation_splicing_pdfs_match(workflow_dir, test_data_dir, pdfs_match):
    result = workflow_dir / Path("test-output/glob-9a503dc39dbe819d5ebf7343f90bb109/feature_aggregation.splicing.pdf")
    expected = test_data_dir / Path("feature_aggregation.splicing.pdf")
    assert pdfs_match(result, expected)


@pytest.mark.workflow("test_segtools_integration")
def test_segtools_feature_aggregation_translation_pdfs_match(workflow_dir, test_data_dir, pdfs_match):
    result = workflow_dir / Path("test-output/glob-9a503dc39dbe819d5ebf7343f90bb109/feature_aggregation.translation.pdf")
    expected = test_data_dir / Path("feature_aggregation.translation.pdf")
    assert pdfs_match(result, expected)
