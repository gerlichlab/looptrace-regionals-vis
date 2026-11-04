"""Points in Euclidean space"""

import dataclasses
import math

from .types import FloatLike


@dataclasses.dataclass(kw_only=True, frozen=True)
class Point3D:
    """Bundle three values as coordinates of point in 3D.

    Parameters
    ----------
    z : FloatLike
        Coordinate in z.
    y : FloatLike
        Coordinate in y.
    x : FloatLike
        Coordinate in x.

    """

    z: FloatLike
    y: FloatLike
    x: FloatLike

    @property
    def _field_names(self) -> list[str]:
        return [f.name for f in dataclasses.fields(self)]

    def __post_init__(self) -> None:
        value_types: dict[str, type] = {
            fn: type(getattr(self, fn)) for fn in self._field_names
        }
        if not all(_is_float_like(t) for t in value_types.values()):
            raise TypeError(
                f"Value of each field of point must be floating-point; got {value_types}"
            )
        if any(math.isnan(getattr(self, fn)) for fn in self._field_names):
            raise ValueError("Cannot use a null numeric as a point coordinate!")
        if any(math.isinf(getattr(self, fn)) for fn in self._field_names):
            raise ValueError("Cannot use an infinite value as a point coordinate!")


def _is_float_like(t: type) -> bool:
    # numpy's float64 subclasses float, so this accepts it too.
    return issubclass(t, float)
