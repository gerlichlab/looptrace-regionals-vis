"""Tests for the correctness of inference of data processing status from filepath"""

import hypothesis as hyp
from hypothesis import strategies as st
import pytest

from looptrace_regionals_vis import find_package_files
from looptrace_regionals_vis.processing import ProcessingStatus


@pytest.mark.parametrize("filepath", find_package_files("examples"))
def test_each_package_example_is_resolvable(filepath):
    assert (
        ProcessingStatus.from_filepath(filepath) is not None
    ), f"Could not infer processing status from filepath: {filepath}"


@hyp.given(arg=st.one_of(st.text(), st.integers(), st.just(None)))
def test_from_filepath_requires_path(arg):
    with pytest.raises(AttributeError):
        ProcessingStatus.from_filepath(arg)


@pytest.mark.parametrize(
    ("get_status", "prep_arg"),
    [
        (ProcessingStatus.from_filename, lambda _, fn: fn),
        (ProcessingStatus.from_filepath, lambda folder, fn: folder / fn),
    ],
)
def test_rois_suffix_is_required(tmp_path, get_status, prep_arg, proc_status_inference_params):
    suffix: str = proc_status_inference_params.suffix
    extension: str = proc_status_inference_params.extension
    arg = prep_arg(tmp_path, f"P0001{suffix}{extension}")
    observed = get_status(arg)
    assert observed == proc_status_inference_params.expectation


@pytest.mark.parametrize(
    ("get_status", "prep_arg"),
    [
        (ProcessingStatus.from_filename, lambda _, fn: fn),
        (ProcessingStatus.from_filepath, lambda folder, fn: folder / fn),
    ],
)
@pytest.mark.parametrize(
    ("extension", "expected"),
    [
        (".unfiltered.csv", None),
        (".csv", ProcessingStatus.Unfiltered),
        (".CSV", None),
        (".proximity_filtered.csv", None),
        (".proximity_labeled.csv", ProcessingStatus.ProximityOnly),
        (".nuclei_filtered.csv", None),
        (".nuclei_labeled.csv", None),
        (".proximity_filtered.nuclei_labeled.csv", ProcessingStatus.ProximityAndNuclei),
    ],
)
def test_standard_csv_extension_is_required(tmp_path, get_status, prep_arg, extension, expected):
    arg = prep_arg(tmp_path, "P0001_rois" + extension)
    observed = get_status(arg)
    assert observed == expected
