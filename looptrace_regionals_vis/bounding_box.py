"""Bounding boxes"""

import dataclasses
from abc import abstractmethod
from collections.abc import Iterable
from math import floor
from typing import Protocol

from numpydoc_decorator import doc  # type: ignore[import-untyped]

from .point import Point3D


class RectangleLike(Protocol):
    """Behaviors related to a rectangle"""

    @abstractmethod
    def get_xMin(self) -> float:
        """'Left' side of rectangle in x"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_xMax(self) -> float:
        """'Right' side of rectangle in x"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_yMin(self) -> float:
        """'Left' side of rectangle in y"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_yMax(self) -> float:
        """'Right' side of rectangle in y"""
        raise NotImplementedError  # pragma: no cover


class RectangularPrismLike(RectangleLike):
    """Behaviors related to a rectangular prism"""

    @abstractmethod
    def get_zMin(self) -> float:
        """'Left' side of rectangle in z"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_zMax(self) -> float:
        """'Right' side of rectangle in z"""
        raise NotImplementedError  # pragma: no cover


@doc(
    summary="A rectangular prism in 3D",
    parameters=dict(
        center="3D center point",
        zMin="Lower bound in z",
        zMax="Upper bound in z",
        yMin="Lower bound in y",
        yMax="Upper bound in y",
        xMin="Lower bound in x",
        xMax="Upper bound in x",
    ),
)
@dataclasses.dataclass(frozen=True, kw_only=True)
class BoundingBox3D(RectangularPrismLike):  # noqa: D101
    center: Point3D
    zMin: float
    zMax: float
    yMin: float
    yMax: float
    xMin: float
    xMax: float

    @classmethod
    def from_flat_arguments(  # type: ignore[no-untyped-def] # noqa: D102
        cls,
        *,
        zc,  # noqa: ANN001
        yc,  # noqa: ANN001
        xc,  # noqa: ANN001
        zMin,  # noqa: ANN001
        zMax,  # noqa: ANN001
        yMin,  # noqa: ANN001
        yMax,  # noqa: ANN001
        xMin,  # noqa: ANN001
        xMax,  # noqa: ANN001
    ) -> "BoundingBox3D":
        point = Point3D(z=zc, y=yc, x=xc)
        return cls(
            center=point,
            zMin=zMin,
            zMax=zMax,
            yMin=yMin,
            yMax=yMax,
            xMin=xMin,
            xMax=xMax,
        )

    @doc(summary="Left side in x dimension")
    def get_xMin(self) -> float:  # noqa: D102
        return self.xMin

    @doc(summary="Right side in x dimension")
    def get_xMax(self) -> float:  # noqa: D102
        return self.xMax

    @doc(summary="Left side in y dimension")
    def get_yMin(self) -> float:  # noqa: D102
        return self.yMin

    @doc(summary="Right side in y dimension")
    def get_yMax(self) -> float:  # noqa: D102
        return self.yMax

    @doc(summary="Left side in z dimension")
    def get_zMin(self) -> float:  # noqa: D102
        return self.zMin

    @doc(summary="Right side in z dimension")
    def get_zMax(self) -> float:  # noqa: D102
        return self.zMax

    def __post_init__(self) -> None:
        """Ensure that each field value is correctly typed and in proper relation to other fields."""
        if self.xMin > self.xMax or self.yMin > self.yMax or self.zMin > self.zMax:
            raise ValueError("For each dimension, min must be no more than max!")
        if (
            self.center.z < self.zMin
            or self.center.z > self.zMax
            or self.center.y < self.yMin
            or self.center.y > self.yMax
            or self.center.x < self.xMin
            or self.center.x > self.xMax
        ):
            raise ValueError("For each dimension, center coordinate must be within min/max bounds!")
        # Avoid repeated computation of the rounded value.
        object.__setattr__(self, "_nearest_z_slice", round(self.center.z))

    def iter_z_slices_nonnegative(
        self,
    ) -> Iterable[tuple[Point3D, Point3D, Point3D, Point3D, bool]]:
        """Stack (1 slice per z) corner points with flag indicating if the slice corresponds to center in z."""
        for z in range(max(0, floor(self.zMin)), max(0, floor(self.zMax) + 1)):
            q1 = Point3D(z=float(z), y=self.yMin, x=self.xMax)
            q2 = Point3D(z=float(z), y=self.yMin, x=self.xMin)
            q3 = Point3D(z=float(z), y=self.yMax, x=self.xMin)
            q4 = Point3D(z=float(z), y=self.yMax, x=self.xMax)
            is_center = z == self._nearest_z_slice  # type: ignore[attr-defined]
            yield q1, q2, q3, q4, is_center
