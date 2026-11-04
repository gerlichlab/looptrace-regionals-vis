"""Bounding boxes"""

import dataclasses
from abc import abstractmethod
from collections.abc import Iterable
from functools import cached_property
from math import floor
from typing import Protocol

from .point import Point3D
from .types import FloatLike


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


@dataclasses.dataclass(frozen=True, kw_only=True)
class BoundingBox3D(RectangularPrismLike):
    """A rectangular prism in 3D.

    Parameters
    ----------
    center : Point3D
        3D center point.
    zMin : float
        Lower bound in z.
    zMax : float
        Upper bound in z.
    yMin : float
        Lower bound in y.
    yMax : float
        Upper bound in y.
    xMin : float
        Lower bound in x.
    xMax : float
        Upper bound in x.

    """

    center: Point3D
    zMin: float
    zMax: float
    yMin: float
    yMax: float
    xMin: float
    xMax: float

    @classmethod
    def from_flat_arguments(  # noqa: D102
        cls,
        *,
        zc: FloatLike,
        yc: FloatLike,
        xc: FloatLike,
        zMin: float,
        zMax: float,
        yMin: float,
        yMax: float,
        xMin: float,
        xMax: float,
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

    def get_xMin(self) -> float:
        """Left side in x dimension.

        Returns
        -------
        float

        """
        return self.xMin

    def get_xMax(self) -> float:
        """Right side in x dimension.

        Returns
        -------
        float

        """
        return self.xMax

    def get_yMin(self) -> float:
        """Left side in y dimension.

        Returns
        -------
        float

        """
        return self.yMin

    def get_yMax(self) -> float:
        """Right side in y dimension.

        Returns
        -------
        float

        """
        return self.yMax

    def get_zMin(self) -> float:
        """Left side in z dimension.

        Returns
        -------
        float

        """
        return self.zMin

    def get_zMax(self) -> float:
        """Right side in z dimension.

        Returns
        -------
        float

        """
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
            raise ValueError(
                "For each dimension, center coordinate must be within min/max bounds!"
            )

    # Avoid repeated computation of the rounded value.
    @cached_property
    def _nearest_z_slice(self) -> int:
        return round(self.center.z)

    def iter_z_slices_nonnegative(
        self,
    ) -> Iterable[tuple[Point3D, Point3D, Point3D, Point3D, bool]]:
        """Stack (1 slice per z) corner points with flag indicating if the slice corresponds to center in z."""
        for z in range(max(0, floor(self.zMin)), max(0, floor(self.zMax) + 1)):
            q1 = Point3D(z=float(z), y=self.yMin, x=self.xMax)
            q2 = Point3D(z=float(z), y=self.yMin, x=self.xMin)
            q3 = Point3D(z=float(z), y=self.yMax, x=self.xMin)
            q4 = Point3D(z=float(z), y=self.yMax, x=self.xMax)
            is_center = z == self._nearest_z_slice
            yield q1, q2, q3, q4, is_center
