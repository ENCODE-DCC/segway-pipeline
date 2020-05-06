import gzip
import hashlib
import subprocess
from pathlib import Path

import pytest


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


def md5sum(file: str) -> str:
    return hashlib.md5(file.encode()).hexdigest()
