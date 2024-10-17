"""Tools for creating the reader of regional points data"""

import dataclasses
import logging
from collections import Counter
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

import numpy as np
import pandas as pd
from numpydoc_decorator import doc  # type: ignore[import-untyped]

from .bounding_box import BoundingBox3D
from .colors import IBM_BLUE, IBM_ORANGE, IBM_PINK, IBM_PURPLE, IBM_YELLOW
from .point import FloatLike, Point3D
from .types import LayerParams, PathOrPaths

FullDataLayer = tuple[list[list[list[int | FloatLike]]], LayerParams, Literal["shapes"]]
Reader = Callable[[PathOrPaths], list[FullDataLayer]]


SHAPE_PARAMS_KEY = "shape_type"
COLOR_PARAMS_KEY = "edge_color"
Z_COLUMN = "zc"
Y_COLUMN = "yc"
X_COLUMN = "xc"
BOX_CENTER_COLUMN_NAMES = [Z_COLUMN, Y_COLUMN, X_COLUMN]
TIME_COLUMN = "timepoint"
CHANNEL_COLUMN = "spotChannel"


class InputFileContentType(Enum):
    """The processing steps undergone by data in a file or in memory"""

    MergeContributors = ".merge_contributors.csv"
    ProximityRejects = ".proximity_rejected.csv"
    NucleiLabeled = ".proximity_accepted.nuclei_labeled.csv"

    @classmethod
    def from_filename(cls, fn: str) -> Optional["InputFileContentType"]:
        """Attempt to infer processing status from given filename."""
        chunks = fn.split(".")
        if not chunks[0].endswith("_rois"):
            logging.debug("There's no ROI-indicative suffix in file basename (%s)", chunks[0])
            return None
        if chunks[-1] != "csv":
            logging.debug("No CSV extension on filename '%s'", fn)
            return None
        for member in cls:
            if fn.endswith(member.value):
                return member
        return None

    @classmethod
    def from_filepath(cls, fp: Path) -> Optional["InputFileContentType"]:
        """Attempt to infer processing status from given filepath."""
        return cls.from_filename(fp.name)


class RoiType(Enum):
    """The type of ROI to display, and in which color"""

    MergeContributor = IBM_BLUE
    DiscardForProximity = IBM_PURPLE
    DiscardForNonNuclearity = IBM_ORANGE
    AcceptedSingleton = IBM_PINK
    AcceptedMerger = IBM_YELLOW

    @property
    def color(self) -> str:
        """More reader-friendly alias for accessing the color associated with the ROI type"""
        return self.value


@doc(
    summary="The main interface for the napari plugin reader contribution",
    parameters=dict(path="Path to file with data to visualise"),
    returns="If the given value can be used by this plugin, a parser function; otherwise, a null value",
)
def get_reader(path: PathOrPaths) -> Optional[Reader]:
    """Get a single-file parser with which to build layer data."""

    def do_not_parse(msg, *, level=logging.DEBUG) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN001
        logging.log(msg=msg, level=level)

    # Check that the given path is indeed a single extant file.
    if isinstance(path, str):
        path: Path = Path(path)  # type: ignore[no-redef]
    if not isinstance(path, Path):
        do_not_parse(f"Can only parse Path, not {type(path).__name__}")
        return None
    if not path.is_dir():
        do_not_parse("Path to parse must exist as directory.")
        return None

    # See if the contents of the folder have at most 1 of each kind of data.
    count_by_kind = Counter(
        InputFileContentType.from_filepath(f) for f in path.iterdir() if _is_plausible_input_file(f)
    )
    if any(n != 1 for n in count_by_kind.values()):
        do_not_parse(
            f"Count of file by data kind doesn't support reading from {path}: {count_by_kind}"
        )
        return None

    # Create the parser.
    def build_layers(folder) -> list[FullDataLayer]:  # type: ignore[no-untyped-def]  # noqa: ANN001
        # Map (uniquely!) each data kind/status to a file to parse.
        file_by_kind: dict[InputFileContentType, Path] = {}
        for fp in filter(_is_plausible_input_file, Path(folder).iterdir()):
            kind = InputFileContentType.from_filepath(fp)
            if kind is None:
                continue
            if kind in file_by_kind:
                # should already be guarded by the decision to parse or not, so it's exceptional.
                raise KeyError(
                    f"Data kind {kind} already found in {folder}: {file_by_kind[kind]}"
                )  # pragma: no cover
            file_by_kind[kind] = fp

        layers: list[FullDataLayer] = []

        for file_type, file_path in file_by_kind.items():
            logging.debug("Processing data for file type %s: %s", file_type.name, file_path)
            time_channel_location_trios: list[
                tuple[int | FloatLike, int | FloatLike, BoundingBox3D]
            ]
            if file_type == InputFileContentType.NucleiLabeled:
                time_channel_location_trios_by_roi_type = _parse_non_contributor_non_proximal_rois(
                    file_path
                )
            else:
                time_channel_location_trios = parse_boxes(file_path)
                if file_type == InputFileContentType.MergeContributors:
                    rt = RoiType.MergeContributor
                elif file_type == InputFileContentType.ProximityRejects:
                    rt = RoiType.DiscardForProximity
                else:
                    raise RuntimeError(
                        f"Unexpected file type (can't determine ROI type)! {file_type}"
                    )
                time_channel_location_trios_by_roi_type = {rt: time_channel_location_trios}

            for (
                roi_type,
                time_channel_location_trios,
            ) in time_channel_location_trios_by_roi_type.items():
                corners: list[list[list[int | FloatLike]]] = []
                shapes: list[str] = []
                for timepoint, channel, box in time_channel_location_trios:
                    for q1, q2, q3, q4, is_center_slice in box.iter_z_slices_nonnegative():
                        corners.append(
                            [[timepoint, channel, *_point_to_list(pt)] for pt in [q1, q2, q3, q4]]
                        )
                        shapes.append("rectangle" if is_center_slice else "ellipse")
                logging.debug("Point count for ROI type %s: %d", roi_type.name, len(corners))
                params: dict[str, object] = {
                    "name": roi_type.name,
                    "shape_type": shapes,
                    "face_color": "transparent",
                    COLOR_PARAMS_KEY: roi_type.color,
                }
                layers.append((corners, params, "shapes"))

        return layers

    return build_layers


@doc(
    summary="Determine if the given path may be an input file to parse.",
    parameters=dict(path="Path to test as a plausible input file"),
    returns="The result of the compound test",
)
def _is_plausible_input_file(path: Path) -> bool:
    return path.is_file() and path.suffix == ".csv" and path.name.split(".")[0].endswith("_rois")


def _parse_non_contributor_non_proximal_rois(
    path: Path,
) -> dict[RoiType, list[tuple[int | FloatLike, int | FloatLike, BoundingBox3D]]]:
    rois_by_type: dict[RoiType, list[tuple[int | FloatLike, int | FloatLike, BoundingBox3D]]] = {}
    for _, row in pd.read_csv(path).iterrows():
        time, channel, loc, is_singleton, is_in_nuc = _parse_nucleus_labeled_record(row)
        if is_in_nuc:
            key = RoiType.AcceptedSingleton if is_singleton else RoiType.AcceptedMerger
        else:
            key = RoiType.DiscardForNonNuclearity
        rois_by_type.setdefault(key, []).append((time, channel, loc))
    return rois_by_type


@doc(
    summary="Read the data from the given file and parse it into bounding boxes.",
    parameters=dict(path="Path to data file from which to parse bounding boxes"),
    returns="List of tuples of time, channel, and box.",
)
def parse_boxes(  # noqa: D103
    path: Path,
) -> list[tuple[int | FloatLike, int | FloatLike, BoundingBox3D]]:
    box_cols = [f.name for f in dataclasses.fields(BoundingBox3D) if f.name != "center"]
    spot_data = pd.read_csv(
        path, usecols=BOX_CENTER_COLUMN_NAMES + box_cols + [TIME_COLUMN, CHANNEL_COLUMN]
    )
    time_channel_location_trios: list[tuple[int | FloatLike, int | FloatLike, BoundingBox3D]] = [
        _parse_time_channel_box_trio(record) for _, record in spot_data.iterrows()
    ]
    return time_channel_location_trios


def _parse_time_channel_box_trio(
    record: dict[str, int | FloatLike] | pd.Series,  # type: ignore[type-arg]
) -> tuple[int | FloatLike, int | FloatLike, BoundingBox3D]:
    record: dict[str, int | float | np.float64] = (  # type: ignore[no-redef]
        record if isinstance(record, dict) else record.to_dict()
    )
    time = record.pop(TIME_COLUMN)
    channel = record.pop(CHANNEL_COLUMN)
    box = BoundingBox3D(
        center=Point3D(z=record["zc"], y=record["yc"], x=record["xc"]),
        zMin=record["zMin"],  # type: ignore[arg-type]
        zMax=record["zMax"],  # type: ignore[arg-type]
        yMin=record["yMin"],  # type: ignore[arg-type]
        yMax=record["yMax"],  # type: ignore[arg-type]
        xMin=record["xMin"],  # type: ignore[arg-type]
        xMax=record["xMax"],  # type: ignore[arg-type]
    )
    return time, channel, box


def _parse_nucleus_labeled_record(
    record: pd.Series,  # type: ignore[type-arg]
) -> tuple[int | FloatLike, int | FloatLike, BoundingBox3D, bool, bool]:
    record: dict[str, int | float | np.float64] = record.to_dict()  # type: ignore[no-redef]
    nuc_num: int = record["nucleusNumber"]
    in_nuc: bool = nuc_num != 0
    is_singleton: bool = record["mergeRois"] is None or pd.isna(record["mergeRois"])
    time, channel, box = _parse_time_channel_box_trio(record)
    return time, channel, box, is_singleton, in_nuc


@doc(
    summary="Flatten point coordinates to list",
    parameters=dict(pt="Point to flatten"),
    returns="[z, y, x]",
)
def _point_to_list(pt: Point3D) -> list[FloatLike]:
    return [pt.z, pt.y, pt.x]
