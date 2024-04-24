"""Tools for creating the reader of regional points data"""

from collections import Counter
from collections.abc import Callable
import dataclasses
import logging
from pathlib import Path
from typing import Literal, Mapping, Optional

from numpydoc_decorator import doc
import pandas as pd

from .bounding_box import BoundingBox3D
from .colors import INDIGO, PALE_SKY_BLUE, PALE_RED_CLAY
from .point import FloatLike, Point3D
from .processing import ProcessingStatus

MappingLike = Mapping[str, object] | pd.Series
LayerParams = dict[str, object]
FullDataLayer = tuple[list[Point3D], LayerParams, Literal["shapes"]]
PathLike = str | Path
PathOrPaths = PathLike | list[PathLike]
Reader = Callable[[PathOrPaths], list[FullDataLayer]]


SHAPE_PARAMS_KEY = "shape_type"
COLOR_PARAMS_KEY = "edge_color"


@doc(
    summary="The main interface for the napari plugin reader contribution",
    parameters=dict(path="Path to file with data to visualise"),
    returns="If the given value can be used by this plugin, a parser function; otherwise, a null value",
)
def get_reader(path: PathOrPaths) -> Optional[Reader]:
    """Get a single-file parser with which to build layer data."""

    def do_not_parse(msg, *, level=logging.DEBUG) -> None:
        logging.log(msg=msg, level=level)

    # Check that the given path is indeed a single extant file.
    if isinstance(path, str):
        path: Path = Path(path)
    if not isinstance(path, Path):
        do_not_parse(f"Can only parse Path, not {type(path).__name__}")
        return None
    if not path.is_dir():
        do_not_parse("Path to parse must exist as directory.")
        return None

    # See if the contents of the folder have 1 of each kind of data.
    count_by_kind = Counter(
        ProcessingStatus.from_filepath(f)
        for f in path.iterdir()
        if f.is_file() and f.suffix == ".csv"
    )
    if any(count_by_kind.get(status, 0) != 1 for status in ProcessingStatus):
        do_not_parse(
            f"Count of file by data kind doesn't support reading from {path}: {count_by_kind}"
        )
        return None

    # Create the parser.
    def build_layers(folder) -> list[FullDataLayer]:
        # Map (uniquely!) each data kind/status to a file to parse.
        file_by_kind: dict[ProcessingStatus, Path] = {}
        for fp in Path(folder).iterdir():
            if not (fp.is_file() and fp.suffix == ".csv"):
                continue
            kind = ProcessingStatus.from_filepath(fp)
            if kind is None:
                continue
            if kind in file_by_kind:
                raise KeyError(f"Data kind {kind} already found in {folder}: {file_by_kind[kind]}")
            file_by_kind[kind] = fp
        if set(file_by_kind.keys()) != set(ProcessingStatus):
            raise ValueError(f"Not all processing statuses found in folder: {folder}")

        layers: list[FullDataLayer] = []

        for status in ProcessingStatus:
            fp = file_by_kind[status]
            boxes = parse_boxes(fp)
            corners: list[list[list[float]]] = []
            shapes: list[str] = []
            for box in boxes:
                for q1, q2, q3, q4, is_center_slice in box.iter_z_slices():
                    corners.append([point_to_list(pt) for pt in [q1, q2, q3, q4]])
                    shapes.append("rectangle" if is_center_slice else "ellipse")
            params: dict[str, object] = {
                "name": fp.stem,
                "shape_type": shapes,
                "face_color": "transparent",
                COLOR_PARAMS_KEY: get_data_color(status),
            }
            layers.append((corners, params, "shapes"))

        return layers

    return build_layers


@doc(
    summary="Get the color to use for the edge of a bounding region.",
    parameters=dict(status="The data processing status for which to get color"),
    raises=dict(ValueError="If the given status doesn't match one of the known values"),
    returns="The color to use for the edge of a bounding region",
)
def get_data_color(status: ProcessingStatus):
    if status == ProcessingStatus.Unfiltered:
        return INDIGO
    if status == ProcessingStatus.ProximityOnly:
        return PALE_SKY_BLUE
    if status == ProcessingStatus.ProximityAndNuclei:
        return PALE_RED_CLAY
    raise ValueError(f"Could not resolve color for data status!")


@doc(
    summary="Read the data from the given file and parse it into bounding boxes.",
    parameters=dict(path="Path to data file from which to parse bounding boxes"),
    returns="A list of bounding boxes, one per record in the given file",
)
def parse_boxes(path: Path) -> list[BoundingBox3D]:
    """Read the bounding boxes (and centroids) from given file."""
    pt_cols = ["zc", "yc", "xc"]
    box_cols = [f.name for f in dataclasses.fields(BoundingBox3D) if f.name != "center"]
    df = pd.read_csv(path, usecols=pt_cols + box_cols)
    boxes = df.apply(lambda row: BoundingBox3D.from_flat_arguments(**row), axis=1)
    return boxes.to_list()


@doc(
    summary="Flatten point coordinates to list",
    parameters=dict(pt="Point to flatten"),
    returns="[z, y, x]",
)
def point_to_list(pt: Point3D) -> list[FloatLike]:
    return [pt.z, pt.y, pt.x]
