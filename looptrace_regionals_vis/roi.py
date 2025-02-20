"""Region of interest (ROI) abstractions"""

from dataclasses import dataclass
from typing import Protocol

from gertils.types import NucleusNumber, TraceIdFrom0

from .bounding_box import BoundingBox3D
from .colors import IBM_BLUE, IBM_ORANGE, IBM_PINK, IBM_PURPLE, IBM_YELLOW
from .types import Channel, RoiId, Timepoint


class RegionOfInterest(Protocol):
    """Attribute each ROI must have to contribute to a Napari layer"""

    @property
    def color(self) -> str:
        """Which color to use for ROIs of this type"""
        ...

    @property
    def typename(self) -> str:
        """The name of the specific ROI subtype"""
        return type(self).__name__


@dataclass(kw_only=True, frozen=True)
class MergeContributorRoi(RegionOfInterest):
    """A ROI which contributed to a merge"""

    id: RoiId
    timepoint: Timepoint
    channel: Channel
    bounding_box: BoundingBox3D
    merge_index: RoiId

    @property
    def color(self) -> str:
        """A merge contributor ROI is blue."""
        return IBM_PURPLE

    def __post_init__(self) -> None:
        if self.id == self.merge_index:
            raise ValueError(f"A {self.__class__.__name__}'s index can't equal its merge_index")


@dataclass(kw_only=True, frozen=True)
class ProximityRejectedRoi(RegionOfInterest):
    """A ROI which was rejected on account of proximity to another ROI"""

    id: RoiId
    timepoint: Timepoint
    channel: Channel
    bounding_box: BoundingBox3D
    neighbors: set[RoiId]

    def __post_init__(self) -> None:
        match self.neighbors:
            case set():
                if len(self.neighbors) == 0:
                    raise ValueError(f"Set of neighbors for {type(self).__name__} is empty")
            case _:
                raise TypeError(
                    f"Expected a set for neighbors for {type(self).__name__} but got {type(self.neighbors).__name__}"
                )

    @property
    def color(self) -> str:
        """A ROI rejected on account of proximity is purple."""
        return IBM_BLUE


@dataclass(kw_only=True, frozen=True)
class NonNuclearRoi(RegionOfInterest):
    """A ROI which was rejected on account of not being in a nucleus"""

    timepoint: Timepoint
    channel: Channel
    bounding_box: BoundingBox3D

    @property
    def color(self) -> str:
        """A ROI rejected on account of non-nuclearity is orange."""
        return IBM_ORANGE


@dataclass(kw_only=True, frozen=True)
class SingletonRoi(RegionOfInterest):
    """A ROI which passed filters and is not the result of a merge"""

    id: RoiId
    timepoint: Timepoint
    channel: Channel
    bounding_box: BoundingBox3D
    traceId: TraceIdFrom0
    trace_partners: set[RoiId]  # which ROIs are part of the same trace
    nucleus_number: NucleusNumber

    @property
    def color(self) -> str:
        """A singleton ROI is pink."""
        return IBM_PINK


@dataclass(kw_only=True, frozen=True)
class MergedRoi(RegionOfInterest):
    """A ROI which passed filters and resulted from a merge"""

    id: RoiId
    timepoint: Timepoint
    channel: Channel
    bounding_box: BoundingBox3D
    contributors: set[RoiId]
    traceId: TraceIdFrom0
    trace_partners: set[RoiId]  # which ROIs are part of the same trace
    nucleus_number: NucleusNumber

    def __post_init__(self) -> None:
        if not isinstance(self.contributors, set):
            raise TypeError(
                f"For a {self.__class__.__name__}, contributors must be set, not {type(self.contributors).__name__}"
            )
        if len(self.contributors) < 2:  # noqa: PLR2004
            raise ValueError(
                f"A {self.__class__.__name__} must have at least 2 contributors, got {len(self.contributors)}"
            )
        if self.id in self.contributors:
            raise ValueError(
                f"A {self.__class__.__name__}'s index can't be in its collection of contributors"
            )

    @property
    def color(self) -> str:
        """A merged ROI is yellow."""
        return IBM_YELLOW
