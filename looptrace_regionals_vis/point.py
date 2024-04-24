"""Points in Euclidean space"""

import dataclasses
import math

import numpy as np
from numpydoc_decorator import doc

FloatLike = float | np.float64


@doc(
    summary="Bundle three values as coordinates of point in 3D",
    parameters=dict(z="z", y="y", x="x"),
)
@dataclasses.dataclass(kw_only=True, frozen=True)
class Point3D:  # noqa: D101
    z: FloatLike
    y: FloatLike
    x: FloatLike

    @property
    def _field_names(self) -> list[str]:
        return [f.name for f in dataclasses.fields(self)]

    def __post_init__(self) -> None:
        value_types = {fn: type(getattr(self, fn)) for fn in self._field_names}
        if not all(_is_float_like(t) for t in value_types.values()):
            raise TypeError(
                f"Value of each field of point must be floating-point; got {value_types}"
            )
        if any(math.isnan(getattr(self, fn)) for fn in self._field_names):
            raise ValueError("Cannot use a null numeric as a point coordinate!")
        if any(math.isinf(getattr(self, fn)) for fn in self._field_names):
            raise ValueError("Cannot use an infinite value as a point coordinate!")


def _is_float_like(t: type) -> bool:
    return issubclass(t, float | np.float64)
