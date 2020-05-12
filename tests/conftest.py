import gzip
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Union

import pytest
from diff_pdf_visually import pdfdiff


@pytest.fixture
def test_data_dir():
    return Path("tests/data")


@pytest.fixture
def genomedatas_match():
    """
    Unfortunately it didn't seem straightforward to use `h5py` to diff the hd5f files, I
    got an error complaining a bit field didn't match to any NumPy type. Instead we just
    run `h5diff` as a subprocess. This requires `h5diff` to be on the PATH.
    """

    def _genomedatas_match(genomedata1: Path, genomedata2: Path) -> bool:
        result = subprocess.run(
            ["h5diff", str(genomedata1), str(genomedata2)], capture_output=True
        )
        return result.returncode == 0 and not result.stdout

    return _genomedatas_match


@pytest.fixture
def traindirs_match(skip_n_lines_md5):
    """
    Within the traindir, the generated shell scripts in the `cmdline` will be
    nondeterministic, since they contain Cromwell file paths. Within `log`, similar
    nondeterminism occurs with the run scripts there and the job logs, however
    jt_info.txt, likelihood.0.tab, and likelihood.1.tab can still be compared (for 2
    parallel training runs). File in the `output` folder seem to have the same contents,
    but the filenames aren't the same so you can't reliably compare them. The files in
    the `triangulation` folder contain a timestamp at line 17, so need to skip that line
    when comparing.
    """

    def _traindirs_match(traindir1: Path, traindir2: Path, workflow_dir: Path) -> bool:
        traindir1_extracted = workflow_dir / "traindir1"
        traindir2_extracted = workflow_dir / "traindir2"
        shutil.unpack_archive(traindir1, extract_dir=traindir1_extracted)
        shutil.unpack_archive(traindir2, extract_dir=traindir2_extracted)
        f2_paths = [i for i in traindir2_extracted.glob("**/*") if i.is_file()]
        for f1 in traindir1_extracted.glob("**/*"):
            if not f1.is_file():
                continue
            if "cmdline" in f1.parts or "output" in f1.parts:
                continue
            if "log" in f1.parts:
                if not f1.match("*.tab") or not f1.match("jt_info.txt"):
                    continue
            shared_root_index = f1.parts.index("traindir")
            f2 = [
                i
                for i in f2_paths
                if i.parts[shared_root_index:] == f1.parts[shared_root_index:]
            ][0]
            if "triangulation" in f1.parts:
                n_lines = 17
                assert skip_n_lines_md5(f1, n_lines) == skip_n_lines_md5(f2, n_lines)
            else:
                assert md5sum(f1) == md5sum(f2)
        return True

    return _traindirs_match


@pytest.fixture
def pdfs_match():
    """
    Fixture to visually diff compare PDFs. Requires pdftocairo executable to be on PATH.
    """

    def _pdfs_match(pdf_1: Path, pdf_2: Path):
        return pdfdiff(str(pdf_1), str(pdf_2))

    return _pdfs_match


@pytest.fixture
def skip_n_lines_md5():
    """
    Text files can sometimes contain nondeterministic data in the headers. This fixture
    returns a function that will compare the md5sums of a file after n lines have been
    skipped. Will decompress gzipped files if need be.
    """

    def _skip_n_lines_md5(file_path: Path, n_lines: int) -> str:
        try:
            with gzip.open(str(file_path), "rt") as f:
                lines = "".join(f.readlines()[n_lines:])
        except OSError:
            with open(str(file_path)) as f:
                lines = "".join(f.readlines()[n_lines:])
        return md5sum(lines)

    return _skip_n_lines_md5


@pytest.fixture
def skip_n_lines_and_compare(skip_n_lines_md5):
    def _skip_n_lines_and_compare(file_1: Path, file_2: Path, n_lines: int) -> bool:
        return skip_n_lines_md5(file_1, n_lines) == skip_n_lines_md5(file_2, n_lines)

    return _skip_n_lines_and_compare


def md5sum(file: Union[str, Path]) -> str:
    """
    Compute the md5sum of a string, a text file, or a binary file.
    """
    if isinstance(file, str):
        return hashlib.md5(file.encode()).hexdigest()
    try:
        with open(file) as f:
            data = f.read()
            return hashlib.md5(data.encode()).hexdigest()
    except UnicodeDecodeError:
        with open(file, "rb") as g:
            binary_data = g.read()
            return hashlib.md5(binary_data).hexdigest()
