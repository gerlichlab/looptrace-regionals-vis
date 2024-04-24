"""Data types related to encoding of data processing steps and status"""

from enum import Enum
import logging
from pathlib import Path
from typing import Optional


class ProcessingStep(Enum):
    """Status of processing of data in a file or in memory"""

    NucleiLabeled = "nuclei_labeled"
    ProximityFiltered = "proximity_filtered"
    ProximityLabeled = "proximity_labeled"

    @classmethod
    def from_string(cls, s: str) -> Optional["ProcessingStep"]:
        """Attempt to parse given string as a processing step."""
        for member in cls:
            if s == member.name or s == member.value:
                return member
        return None


class ProcessingStatus(Enum):
    """The processing steps undergone by data in a file or in memory"""

    Unfiltered = tuple()
    ProximityOnly = (ProcessingStep.ProximityLabeled,)
    ProximityAndNuclei = (
        ProcessingStep.ProximityFiltered,
        ProcessingStep.NucleiLabeled,
    )

    @classmethod
    def from_filename(cls, fn: str) -> Optional["ProcessingStatus"]:
        """Attempt to infer processing status from given filename."""
        chunks = fn.split(".")
        if not chunks[0].endswith("_rois"):
            logging.debug(f"There's no ROI-indicative suffix in file basename ({chunks[0]})")
            return None
        if chunks[-1] != "csv":
            logging.debug(f"No CSV extension on filename '{fn}'")
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
