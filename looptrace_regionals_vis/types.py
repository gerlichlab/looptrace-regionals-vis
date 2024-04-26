"""General custom data types"""

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

LayerParams = dict[str, object]
MappingLike = Mapping[str, object] | pd.Series
PathLike = str | Path
PathOrPaths = PathLike | list[PathLike]
