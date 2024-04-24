"""Parameterizations and helpers for tests related to building a reader"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from numpydoc_decorator import doc

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
        ("", ".proximity_filtered.nuclei_labeled.csv", None),
        ("_rois", "", None),
        ("_rois", ".csv", ProcessingStatus.Unfiltered),
        ("_rois", ".CSV", None),
        ("_rois", ".proximity_filtered.csv", None),
        ("_rois", ".proximity_labeled.csv", ProcessingStatus.ProximityOnly),
        ("_rois", ".proximity_filtered.nuclei_labeled.csv", ProcessingStatus.ProximityAndNuclei),
        ("_rois", ".proximity_labeled.nuclei_labeled.csv", None),
        ("_rois", ".proximity_labeled.csv", ProcessingStatus.ProximityOnly),
    ]
]


def pytest_generate_tests(metafunc):
    """Facilitate parametric dynamism in tests."""
    if "proc_status_inference_params" in metafunc.fixturenames:
        metafunc.parametrize(
            "proc_status_inference_params", PROCESSING_STATUS_INFERENCE_PARAMETERIZATIONS
        )
