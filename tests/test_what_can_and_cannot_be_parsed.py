"""Validation of what this plugin will or will not attempt to parse"""

import itertools
import shutil
from pathlib import Path
import pytest

from looptrace_regionals_vis import get_package_examples_folder, list_package_example_files
from looptrace_regionals_vis.reader import get_reader


EXAMPLE_FILES = list_package_example_files()


def test_cannot_read_list_of_files():
    assert (
        get_reader(EXAMPLE_FILES) is None
    ), "Expected inability to parse list of filepaths, but got non-null reader!"


@pytest.mark.parametrize("wrap", (str, Path))
def test_would_read_collectivity_of_package_examples(wrap):
    folder = wrap(get_package_examples_folder())
    assert callable(
        get_reader(folder)
    ), f"Expected a callable reader for path {folder} but didn't get one!"


@pytest.mark.parametrize("wrap", (str, Path))
@pytest.mark.parametrize(
    "what_to_copy",
    [
        combo
        for k in range(len(list_package_example_files()))
        for combo in itertools.combinations(EXAMPLE_FILES, k)
    ],
)
def test_would_not_read_package_examples_if_not_existing(tmp_path, wrap, what_to_copy):
    for filepath in what_to_copy:
        shutil.copy(filepath, tmp_path)
    num_temp_files = sum(1 for _ in tmp_path.iterdir())
    assert num_temp_files == len(
        what_to_copy
    ), f"Was copying {len(what_to_copy)} file(s), but test case tempdir now has {num_temp_files}"
    arg = wrap(tmp_path)
    assert (
        get_reader(arg) is None
    ), f"Expected inability to parse list of filepaths, but got non-null reader for {arg}!"
