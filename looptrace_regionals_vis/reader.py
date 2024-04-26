"""Tools for creating the reader of regional points data"""

from collections import Counter
from collections.abc import Callable
import dataclasses
import logging
import os
from pathlib import Path
from typing import Literal, Optional

from gertils.types import TimepointFrom0
from numpydoc_decorator import doc
import pandas as pd

from .bounding_box import BoundingBox3D
from .point import FloatLike, Point3D
from .processing import ProcessingStatus
from .types import LayerParams, PathOrPaths

FullDataLayer = tuple[list[list[FloatLike]], LayerParams, Literal["shapes"]]
Reader = Callable[[PathOrPaths], list[FullDataLayer]]


SHAPE_PARAMS_KEY = "shape_type"
COLOR_PARAMS_KEY = "edge_color"
BOX_CENTER_COLUMN_NAMES = ["zc", "yc", "xc"]
TIME_COLUMN = "frame"
CHANNEL_COLUMN = "ch"


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

        layers: list[FullDataLayer] = []

        for status, fp in file_by_kind.items():
            logging.debug("Processing data for status %s: %s", status.name, fp)
            inferred_status, boxes = parse_boxes(fp)
            if inferred_status != status:  # This should never happen
                raise RuntimeError(
                    f"File {fp} had been deemed {status} but then was parsed as {inferred_status}"
                )
            corners: list[list[list[int | float]]] = []
            shapes: list[str] = []
            for timepoint, channel, box in boxes:
                if box is None:
                    continue
                for q1, q2, q3, q4, is_center_slice in box.iter_z_slices():
                    corners.append([[timepoint, channel] + point_to_list(pt) for pt in [q1, q2, q3, q4]])
                    shapes.append("rectangle" if is_center_slice else "ellipse")
            logging.debug("Point count for status %s: %d", status.name, len(corners))
            params: dict[str, object] = {
                "name": fp.stem,
                "shape_type": shapes,
                "face_color": "transparent",
                COLOR_PARAMS_KEY: status.color,
            }
            layers.append((corners, params, "shapes"))

        return layers

    return build_layers


@doc(
    summary="Read the data from the given file and parse it into bounding boxes.",
    parameters=dict(path="Path to data file from which to parse bounding boxes"),
    raises=dict(ValueError="If data kind/status can't be inferred from given path"),
)
def parse_boxes(path: Path) -> tuple[ProcessingStatus, list[tuple[TimepointFrom0, Optional[BoundingBox3D]]]]:
    status = ProcessingStatus.from_filepath(path)
    if status is None:
        raise ValueError(f"Could not infer data kind/status from path: {path}")
    box_cols = [f.name for f in dataclasses.fields(BoundingBox3D) if f.name != "center"]
    spot_data = pd.read_csv(path, usecols=BOX_CENTER_COLUMN_NAMES + box_cols + [TIME_COLUMN, CHANNEL_COLUMN])
    time_channel_box_trios: list[tuple[TimepointFrom0, int, Optional[BoundingBox3D]]] = []
    for _, record in spot_data.iterrows():
        data = record.to_dict() if isinstance(record, pd.Series) else record
        time = data.pop(TIME_COLUMN)
        channel = data.pop(CHANNEL_COLUMN)
        box = status.record_to_box(data)
        time_channel_box_trios.append((time, channel, box))
    return status, time_channel_box_trios


@doc(
    summary="Flatten point coordinates to list",
    parameters=dict(pt="Point to flatten"),
    returns="[z, y, x]",
)
def point_to_list(pt: Point3D) -> list[FloatLike]:
    return [pt.z, pt.y, pt.x]
