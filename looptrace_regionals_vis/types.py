"""General custom data types"""

from pathlib import Path

LayerParams = dict[str, object]
PathLike = str | Path
PathOrPaths = PathLike | list[PathLike]
