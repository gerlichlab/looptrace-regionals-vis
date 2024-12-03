"""General custom data types"""

from pathlib import Path

import numpy as np

Channel = int
FloatLike = float | np.float64
LayerParams = dict[str, object]
PathLike = str | Path
PathOrPaths = PathLike | list[PathLike]
RoiId = int
Timepoint = int
