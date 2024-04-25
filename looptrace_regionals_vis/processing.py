"""Data types related to encoding of data processing steps and status"""

from enum import Enum
import logging
from pathlib import Path
from typing import Optional

from numpydoc_decorator import doc
import pandas as pd

from .bounding_box import BoundingBox3D
from .colors import INDIGO, PALE_RED_CLAY, PALE_SKY_BLUE
from .types import MappingLike


class ProcessingStep(Enum):
    """Status of processing of data in a file or in memory"""

    NucleiFiltration = "nuclei_filtration"
    ProximityFiltration = "proximity_filtration"

    @property
    def filename_extension(self) -> str:
        """Get the representation of this step in a filename extension."""
        if self == self.__class__.NucleiFiltration:
            return "nuclei_filtered"
        if self == self.__class__.ProximityFiltration:
            return "proximity_filtered"
        raise ValueError(f"Unsupported processing step: {self}")

    @classmethod
    def from_string(cls, s: str) -> Optional["ProcessingStep"]:
        """Attempt to parse given string as a processing step."""
        for member in cls:
            if s == member.name or s == member.value or s == member.filename_extension:
                return member
        return None


class ProcessingStatus(Enum):
    """The processing steps undergone by data in a file or in memory"""

    Unfiltered = tuple()
    ProximityFiltered = (ProcessingStep.ProximityFiltration,)
    ProximityAndNucleiFiltered = (
        ProcessingStep.ProximityFiltration,
        ProcessingStep.NucleiFiltration,
    )

    @property
    def color(self) -> str:
        "Get the color for Napari for this status."
        if self == self.__class__.Unfiltered:
            return INDIGO
        if self == self.__class__.ProximityFiltered:
            return PALE_SKY_BLUE
        if self == self.__class__.ProximityAndNucleiFiltered:
            return PALE_RED_CLAY
        # This is included only for completeness and should never happen.
        raise ValueError(f"Unsupported spot kind/status: {self}")  # pragma: no cover

    @doc(
        summary="Decide whether to use the given record.",
        parameters=dict(record="Record (e.g., row from CSV) of data to consider for building box."),
    )
    def record_to_box(self, record: MappingLike) -> Optional[BoundingBox3D]:
        data = record.to_dict() if isinstance(record, pd.Series) else record
        return BoundingBox3D.from_flat_arguments(**data)

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
