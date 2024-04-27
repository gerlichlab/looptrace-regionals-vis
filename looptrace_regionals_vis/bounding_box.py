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
    def get_x_min(self) -> float:
        """'Left' side of rectangle in x"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_x_max(self) -> float:
        """'Right' side of rectangle in x"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_y_min(self) -> float:
        """'Left' side of rectangle in y"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_y_max(self) -> float:
        """'Right' side of rectangle in y"""
        raise NotImplementedError  # pragma: no cover


class RectangularPrismLike(RectangleLike):
    """Behaviors related to a rectangular prism"""

    @abstractmethod
    def get_z_min(self) -> float:
        """'Left' side of rectangle in z"""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_z_max(self) -> float:
        """'Right' side of rectangle in z"""
        raise NotImplementedError  # pragma: no cover


@doc(
    summary="A rectangular prism in 3D",
    parameters=dict(
        center="3D center point",
        z_min="Lower bound in z",
        z_max="Upper bound in z",
        y_min="Lower bound in y",
        y_max="Upper bound in y",
        x_min="Lower bound in x",
        x_max="Upper bound in x",
    ),
)
@dataclasses.dataclass(frozen=True, kw_only=True)
class BoundingBox3D(RectangularPrismLike):  # noqa: D101
    center: Point3D
    z_min: float
    z_max: float
    y_min: float
    y_max: float
    x_min: float
    x_max: float

    @classmethod
    def from_flat_arguments(  # type: ignore[no-untyped-def] # noqa: D102
        cls,
        *,
        zc,  # noqa: ANN001
        yc,  # noqa: ANN001
        xc,  # noqa: ANN001
        z_min,  # noqa: ANN001
        z_max,  # noqa: ANN001
        y_min,  # noqa: ANN001
        y_max,  # noqa: ANN001
        x_min,  # noqa: ANN001
        x_max,  # noqa: ANN001
    ) -> "BoundingBox3D":
        point = Point3D(z=zc, y=yc, x=xc)
        return cls(
            center=point,
            z_min=z_min,
            z_max=z_max,
            y_min=y_min,
            y_max=y_max,
            x_min=x_min,
            x_max=x_max,
        )

    @doc(summary="Left side in x dimension")
    def get_x_min(self) -> float:  # noqa: D102
        return self.x_min

    @doc(summary="Right side in x dimension")
    def get_x_max(self) -> float:  # noqa: D102
        return self.x_max

    @doc(summary="Left side in y dimension")
    def get_y_min(self) -> float:  # noqa: D102
        return self.y_min

    @doc(summary="Right side in y dimension")
    def get_y_max(self) -> float:  # noqa: D102
        return self.y_max

    @doc(summary="Left side in z dimension")
    def get_z_min(self) -> float:  # noqa: D102
        return self.z_min

    @doc(summary="Right side in z dimension")
    def get_z_max(self) -> float:  # noqa: D102
        return self.z_max

    def __post_init__(self) -> None:
        """Ensure that each field value is correctly typed and in proper relation to other fields."""
        if self.x_min > self.x_max or self.y_min > self.y_max or self.z_min > self.z_max:
            raise ValueError("For each dimension, min must be no more than max!")
        if (
            self.center.z < self.z_min
            or self.center.z > self.z_max
            or self.center.y < self.y_min
            or self.center.y > self.y_max
            or self.center.x < self.x_min
            or self.center.x > self.x_max
        ):
            raise ValueError("For each dimension, center coordinate must be within min/max bounds!")
        # Avoid repeated computation of the rounded value.
        object.__setattr__(self, "_nearest_z_slice", round(self.center.z))

    def iter_z_slices_nonnegative(
        self,
    ) -> Iterable[tuple[Point3D, Point3D, Point3D, Point3D, bool]]:
        """Stack (1 slice per z) corner points with flag indicating if the slice corresponds to center in z."""
        for z in range(max(0, floor(self.z_min)), max(0, floor(self.z_max) + 1)):
            q1 = Point3D(z=float(z), y=self.y_min, x=self.x_max)
            q2 = Point3D(z=float(z), y=self.y_min, x=self.x_min)
            q3 = Point3D(z=float(z), y=self.y_max, x=self.x_min)
            q4 = Point3D(z=float(z), y=self.y_max, x=self.x_max)
            is_center = z == self._nearest_z_slice  # type: ignore[attr-defined]
            yield q1, q2, q3, q4, is_center
