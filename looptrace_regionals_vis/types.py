"""General custom data types"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

Channel = int
FloatLike = float | np.float64
LayerParams = dict[str, object]
PathLike = str | Path
PathOrPaths = PathLike | list[PathLike]
RoiIndex = int
Timepoint = int


@dataclass(frozen=True)
class NucleusNumber:
    """Wrap a positive integer as indicating a particular nucleus."""

    get: int

    def __post_init__(self) -> None:
        if self.get < 1:
            raise ValueError(
                f"A nucleus number must be a strictly positive integer, not ({type(self.get).__name__}) {self.get}"
            )
