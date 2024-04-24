"""Regression tests for processing step inference from file name/path"""

import pytest

from looptrace_regionals_vis.processing import ProcessingStatus


@pytest.mark.parametrize(
    ("funcname", "init_arg", "prep_arg", "expected"),
    [
        ("from_filename", "P0001_rois.unfiltered.csv", lambda _, fn: fn, None),
        ("from_filepath", "P0001_rois.unfiltered.csv", lambda folder, fn: folder / fn, None),
        ("from_filename", "P0001_rois.csv", lambda _, fn: fn, ProcessingStatus.Unfiltered),
        (
            "from_filepath",
            "P0001_rois.csv",
            lambda folder, fn: folder / fn,
            ProcessingStatus.Unfiltered,
        ),
    ],
)
def test_explicit_unfiltered_cannot_by_resolved(tmp_path, funcname, init_arg, prep_arg, expected):
    """The filename must OMIT processing steps, NOT note 'unfiltered'."""
    arg = prep_arg(tmp_path, init_arg)
    observed = getattr(ProcessingStatus, funcname)(arg)
    assert observed == expected
