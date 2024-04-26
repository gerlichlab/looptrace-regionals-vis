import os
from pathlib import Path
import dask.array as da

from .types import PathLike
PathOrPaths = PathLike | list[PathLike]


TIMEPOINTS_ENV_VAR = "LOOPTRACE_REGIONAL_TIMEPOINTS"

def get_reader(path: PathOrPaths):
    
    if isinstance(path, str):
        path = Path(Path)
    if not isinstance(path, Path):
        return None
    if not path.is_dir():
        return None
    if not path.suffix == ".zarr":
        return None
    
    reg_times_raw: str = os.getenv(TIMEPOINTS_ENV_VAR, "")
    if reg_times_raw == "":
        return None
    try:
        time_init_raw, time_final_raw = reg_times_raw.split("-")
    except ValueError:
        return None
    try:
        t_i, t_f = int(time_init_raw), int(time_final_raw)
    except (TypeError, ValueError):
        return None
    if t_i < 0 or t_f < 0:
        return None
    if t_i >= t_f:
        return None

    def read_data(p):
        img = da.from_zarr(p / "0")
        return img[t_i:(t_f + 1)]
    
    return lambda p: (read_data(p), {}, "image")
