"""Tests for the correctness of inference of data processing status from filepath"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import hypothesis as hyp
import pytest
from hypothesis import strategies as st
from numpydoc_decorator import doc  # type: ignore[import-untyped]

from looptrace_regionals_vis import find_package_files
from looptrace_regionals_vis.reader import InputFileContentType


@doc(
    summary="Bundle filename suffix, extension, and expected inference of processing status",
    parameters=dict(
        suffix="Part of the filename just before the extension",
        extension="The extension to use for the filename/filepath",
        expectation="The expected inferred processing status (if on's expected)",
    ),
)
@dataclass(kw_only=True, frozen=True)
class FileTypeInferenceParameterization:
    suffix: str
    extension: str
    expectation: Optional[InputFileContentType]

    def make_filename(self, *, prefix: str) -> str:
        """Create a filename by concatenating given prefix with stored suffix and extension."""
        return prefix + self.suffix + self.extension

    def make_filepath(self, *, folder: Path, prefix: str) -> Path:
        """Create a filename by joining given concatenation of given prefix, stored suffix and extension with given folder."""
        return folder / self.make_filename(prefix=prefix)


@pytest.mark.parametrize("filepath", find_package_files("examples"))
def test_each_package_example_is_resolvable(filepath):
    assert (
        InputFileContentType.from_filepath(filepath) is not None
    ), f"Could not infer processing status from filepath: {filepath}"


@hyp.given(arg=st.one_of(st.text(), st.integers(), st.just(None)))
def test_from_filepath_requires_path(arg):
    with pytest.raises(AttributeError):
        InputFileContentType.from_filepath(arg)


@pytest.mark.parametrize(
    ("get_status", "prep_arg"),
    [
        (InputFileContentType.from_filename, lambda _, fn: fn),
        (InputFileContentType.from_filepath, lambda folder, fn: folder / fn),
    ],
)
@pytest.mark.parametrize(
    "file_type_inference_params",
    [
        FileTypeInferenceParameterization(suffix=suffix, extension=ext, expectation=exp)
        for suffix, ext, exp in [
            ("", ".unfiltered.csv", None),
            ("", ".proximity_accepted.csv", None),
            ("", ".proximity_rejected.csv", None),
            ("", ".proximity_accepted.nuclei_labeled.csv", None),
            ("", ".proximity_rejected.nuclei_labeled.csv", None),
            ("", ".with_trace_ids.csv", None),
            ("", ".merge_contributors.csv", None),
            ("_rois", "", None),
            ("_rois", ".CSV", None),
            ("_rois", ".merge_contributors.csv", InputFileContentType.MergeContributors),
            ("_rois", ".proximity_rejected.csv", InputFileContentType.ProximityRejects),
            ("_rois", ".proximity_accepted.csv", None),
            ("_rois", ".proximity_rejected.nuclei_labeled.csv", None),
            ("_rois", ".proximity_accepted.nuclei_labeled.csv", None),
            ("_rois", ".with_trace_ids.csv", InputFileContentType.NucleiLabeled),
            ("_rois", ".csv", None),
            ("_rois", ".nuclei_labeled.proximity_accepted.csv", None),
        ]
    ],
)
def test_rois_suffix_is_required(tmp_path, get_status, prep_arg, file_type_inference_params):
    suffix: str = file_type_inference_params.suffix
    extension: str = file_type_inference_params.extension
    arg = prep_arg(tmp_path, f"P0001{suffix}{extension}")
    observed = get_status(arg)
    assert observed == file_type_inference_params.expectation
