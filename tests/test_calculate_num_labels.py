import builtins
from contextlib import suppress as does_not_raise
from typing import List

import pytest

from segway.calculate_num_labels import calculate_num_labels, get_parser, main


@pytest.mark.parametrize(
    "args,condition",
    [
        (["--num-tracks", "3", "-o", "num_labels.txt"], does_not_raise()),
        (["-o", "mylabels.txt"], pytest.raises(SystemExit)),
        (["--num-tracks", "3"], pytest.raises(SystemExit)),
    ],
)
def test_get_parser(args: List[str], condition):
    parser = get_parser()
    with condition:
        parser.parse_args(args)


def test_calculate_num_labels():
    result = calculate_num_labels(16)
    assert result == 18


def test_main(mocker):
    testargs = ["prog", "--num-tracks", "4", "-o", "numlabels.txt"]
    mocker.patch("sys.argv", testargs)
    mocker.patch("builtins.open", mocker.mock_open())
    main()
    assert builtins.open.mock_calls[2][1][0] == 14
