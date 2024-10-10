"""Tests for the accuracy and robustness of parsing bounding boxes"""

import itertools

import pandas as pd
import pytest

from looptrace_regionals_vis import find_package_files
from looptrace_regionals_vis.reader import BOX_CENTER_COLUMN_NAMES, parse_boxes


@pytest.mark.parametrize("spots_file", find_package_files("examples"))
def test_parsed_box_count_is_one_less_than_line_count(spots_file):
    boxes = parse_boxes(spots_file)
    with spots_file.open() as fh:
        num_lines = sum(1 for _ in fh)
    assert len(boxes) == num_lines - 1


@pytest.mark.parametrize("spots_file", find_package_files("examples"))
@pytest.mark.parametrize(
    "drop_cols",
    [
        cols
        for k in range(1, len(BOX_CENTER_COLUMN_NAMES) + 1)
        for cols in itertools.combinations(BOX_CENTER_COLUMN_NAMES, k)
    ],
)
def test_cannot_parse_boxes_without_center(tmp_path, spots_file, drop_cols):
    target = tmp_path / spots_file.name
    pd.read_csv(spots_file, index_col=0).drop(list(drop_cols), axis=1).to_csv(target)

    # We expect an error because of a request to read specific columns (usecols) that will now be absent (having been removed).
    with pytest.raises(ValueError) as error_context:  # noqa: PT011
        parse_boxes(target)
    assert str(error_context.value).startswith(
        "Usecols do not match columns, columns expected but not found"
    )


@pytest.mark.parametrize("spots_file", find_package_files("examples"))
def test_parse_is_robust_to_presence_or_absence_of_index_column(tmp_path, spots_file):
    boxes_1 = parse_boxes(spots_file)
    target = tmp_path / spots_file.name
    pd.read_csv(spots_file, index_col=0).to_csv(target, index=False)
    boxes_2 = parse_boxes(target)
    assert len(boxes_1) == len(boxes_2)
    assert boxes_1 == boxes_2
