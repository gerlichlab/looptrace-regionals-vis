"""Tests for the correctness of inference of data processing status from filepath"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import hypothesis as hyp
from hypothesis import strategies as st
import pytest

from numpydoc_decorator import doc

from looptrace_regionals_vis import find_package_files
from looptrace_regionals_vis.processing import ProcessingStatus


@doc(
    summary="Bundle filename suffix, extension, and expected inference of processing status",
    parameters=dict(
        suffix="Part of the filename just before the extension",
        extension="The extension to use for the filename/filepath",
        expectation="The expected inferred processing status (if on's expected)",
    ),
)
@dataclass(kw_only=True, frozen=True)
class ProcessingStatusInferenceParameterization:  # noqa: D101
    suffix: str
    extension: str
    expectation: Optional[ProcessingStatus]

    def make_filename(self, *, prefix: str) -> str:
        """Create a filename by concatenating given prefix with stored suffix and extension."""
        return prefix + self.suffix + self.extension

    def make_filepath(self, *, folder: Path, prefix: str) -> Path:
        """Create a filename by joining given concatenation of given prefix, stored suffix and extension with given folder."""
        return folder / self.make_filename(prefix=prefix)


PROCESSING_STATUS_INFERENCE_PARAMETERIZATIONS = [
    ProcessingStatusInferenceParameterization(suffix=suffix, extension=ext, expectation=exp)
    for suffix, ext, exp in [
        ("", ".unfiltered.csv", None),
        ("", ".proximity_filtered.csv", None),
        ("", ".proximity_labeled.csv", None),
        ("", ".proximity_filtered.nuclei_filtered.csv", None),
        ("", ".proximity_labeled.nuclei_labeled.csv", None),
        ("", ".proximity_filtered.nuclei_labeled.csv", None),
        ("", ".proximity_labeled.nuclei_filtered.csv", None),
        ("_rois", "", None),
        ("_rois", ".CSV", None),
        ("_rois", ".proximity_labeled.csv", None),
        ("_rois", ".proximity_labeled.nuclei_labeled.csv", None),
        ("_rois", ".proximity_filtered.nuclei_labeled.csv", None),
        ("_rois", ".proximity_labeled.nuclei_filtered.csv", None),
        ("_rois", ".csv", ProcessingStatus.Unfiltered),
        ("_rois", ".proximity_filtered.csv", ProcessingStatus.ProximityFiltered),
        (
            "_rois",
            ".proximity_filtered.nuclei_filtered.csv",
            ProcessingStatus.ProximityAndNucleiFiltered,
        ),
        ("_rois", ".nuclei_filtered.proximity_labeled.csv", None),
    ]
]


def pytest_generate_tests(metafunc):
    """Facilitate parametric dynamism in tests."""
    if "proc_status_inference_params" in metafunc.fixturenames:
        metafunc.parametrize(
            "proc_status_inference_params", PROCESSING_STATUS_INFERENCE_PARAMETERIZATIONS
        )


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
        (".proximity_labeled.csv", None),
        (".proximity_filtered.csv", ProcessingStatus.ProximityFiltered),
        (".nuclei_labeled.csv", None),
        (".nuclei_filtered.csv", None),
        (".proximity_filtered.nuclei_filtered.csv", ProcessingStatus.ProximityAndNucleiFiltered),
    ],
)
def test_standard_csv_extension_is_required(tmp_path, get_status, prep_arg, extension, expected):
    arg = prep_arg(tmp_path, "P0001_rois" + extension)
    observed = get_status(arg)
    assert observed == expected
