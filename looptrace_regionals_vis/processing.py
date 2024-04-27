"""Data types related to encoding of data processing steps and status"""

import logging
from enum import Enum
from pathlib import Path
from typing import Optional

from .colors import INDIGO, PALE_RED_CLAY, PALE_SKY_BLUE


class ProcessingStep(Enum):
    """Status of processing of data in a file or in memory"""

    NucleiFiltration = "nuclei_filtration"
    ProximityFiltration = "proximity_filtration"

    @property
    def filename_extension(self) -> str:
        """Get the representation of this step in a filename extension."""
        if self == ProcessingStep.NucleiFiltration:
            return "nuclei_filtered"
        if self == ProcessingStep.ProximityFiltration:
            return "proximity_filtered"
        # This is included only for completeness and should never happen.
        raise ValueError(f"Unsupported processing step: {self}")  # pragma: no cover

    @classmethod
    def from_string(cls, s: str) -> Optional["ProcessingStep"]:
        """Attempt to parse given string as a processing step."""
        for member in cls:
            if s in {member.name, member.value, member.filename_extension}:
                return member
        return None


class ProcessingStatus(Enum):
    """The processing steps undergone by data in a file or in memory"""

    Unfiltered = tuple()  # type: ignore[var-annotated]
    ProximityFiltered = (ProcessingStep.ProximityFiltration,)
    ProximityAndNucleiFiltered = (
        ProcessingStep.ProximityFiltration,
        ProcessingStep.NucleiFiltration,
    )

    @property
    def color(self) -> str:
        "Get the color for Napari for this status."
        if self == ProcessingStatus.Unfiltered:
            return INDIGO
        if self == ProcessingStatus.ProximityFiltered:
            return PALE_SKY_BLUE
        if self == ProcessingStatus.ProximityAndNucleiFiltered:
            return PALE_RED_CLAY
        # This is included only for completeness and should never happen.
        raise ValueError(f"Unsupported spot kind/status: {self}")  # pragma: no cover

    @classmethod
    def from_filename(cls, fn: str) -> Optional["ProcessingStatus"]:
        """Attempt to infer processing status from given filename."""
        chunks = fn.split(".")
        if not chunks[0].endswith("_rois"):
            logging.debug("There's no ROI-indicative suffix in file basename (%s)", chunks[0])
            return None
        if chunks[-1] != "csv":
            logging.debug("No CSV extension on filename '%s'", fn)
            return None
        steps = tuple(ProcessingStep.from_string(c) for c in chunks[1:-1])
        for member in cls:
            if member.value == steps:
                return member
        return None

    @classmethod
    def from_filepath(cls, fp: Path) -> Optional["ProcessingStatus"]:
        """Attempt to infer processing status from given filepath."""
        return cls.from_filename(fp.name)
