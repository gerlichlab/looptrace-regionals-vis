"""Tools for creating the reader of regional points data"""

import logging
from collections import Counter
from collections.abc import Callable, Sized
from enum import Enum
from pathlib import Path
from typing import Literal, Optional, TypeAlias

import pandas as pd
from gertils.types import NucleusNumber, TraceIdFrom0
from numpydoc_decorator import doc  # type: ignore[import-untyped]
from pandas.errors import EmptyDataError

from .bounding_box import BoundingBox3D
from .point import FloatLike, Point3D
from .roi import MergeContributorRoi, MergedRoi, NonNuclearRoi, ProximityRejectedRoi, SingletonRoi
from .settings import (
    display_roi_id_for_singletons,
    get_maximum_number_of_proximity_partners_to_display,
)
from .types import Channel, LayerParams, PathOrPaths, RoiId, Timepoint

# Aliases
FullDataLayer = tuple[list[list[list[int | FloatLike]]], LayerParams, Literal["shapes"]]
IdAndContributors = tuple[RoiId, set[RoiId]]
Reader = Callable[[PathOrPaths], list[FullDataLayer]]

# Constants
Z_COLUMN = "zc"
Y_COLUMN = "yc"
X_COLUMN = "xc"
BOX_CENTER_COLUMN_NAMES = [Z_COLUMN, Y_COLUMN, X_COLUMN]
CHANNEL_COLUMN = "spotChannel"
COLOR_PARAMS_KEY = "edge_color"
ROI_ID_COLUMN = "index"
SHAPE_PARAMS_KEY = "shape_type"
TEXT_SIZE = 8
TIME_COLUMN = "timepoint"
TOO_CLOSE_ROIS_COLUMN: str = "tooCloseRois"


class InputFileContentType(Enum):
    """The processing steps undergone by data in a file or in memory"""

    MergeContributors = ".merge_contributors.csv"
    ProximityRejects = ".proximity_rejected.csv"
    NucleiLabeled = ".with_trace_ids.csv"

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


@doc(
    summary="The main interface for the napari plugin reader contribution",
    parameters=dict(path="Path to file with data to visualise"),
    returns="If the given value can be used by this plugin, a parser function; otherwise, a null value",
)
def get_reader(path: PathOrPaths) -> Optional[Reader]:  # noqa: PLR0915
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
    def build_layers(folder) -> list[FullDataLayer]:  # type: ignore[no-untyped-def]  # noqa: ANN001 PLR0915
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

        # Each file type may have a particular parse strategy.
        for file_type, file_path in file_by_kind.items():
            logging.debug("Processing data for file type %s: %s", file_type.name, file_path)
            if file_type == InputFileContentType.MergeContributors:
                parse_result: list[MergeContributorRoi]
                try:
                    data = pd.read_csv(file_path)
                except EmptyDataError:
                    logging.warning("Empty data file: %s", file_path)
                    parse_result = []
                else:
                    parse_result = [
                        _parse_merge_contributor_record(row) for _, row in data.iterrows()
                    ]
                rois_by_type = {MergeContributorRoi: parse_result}
            elif file_type == InputFileContentType.NucleiLabeled:
                rois_by_type = {}
                for r in _parse_non_contributor_non_proximal_rois(file_path):
                    # Ignore type check here since we can't properly disambiguate the subcases
                    # w.r.t. ROI type.
                    rois_by_type.setdefault(type(r), []).append(r)  # type: ignore[arg-type]
            elif file_type == InputFileContentType.ProximityRejects:
                rois_by_type = {
                    ProximityRejectedRoi: [  # type: ignore[dict-item]
                        ProximityRejectedRoi(
                            id=i,
                            timepoint=t,
                            channel=c,
                            bounding_box=b,
                            neighbors=ns,
                        )  # type: ignore[misc]
                        for i, ns, t, c, b in _parse_proximity_rejects(file_path)
                    ]
                }
            else:
                raise RuntimeError(f"Unexpected file type (can't determine ROI type)! {file_type}")

            # For some file types, this loop is trivial (single-element rois_by_type).
            for roi_type, rois in rois_by_type.items():
                try:
                    layer_color: str = rois[0].color
                except IndexError:
                    logging.warning(f"No ROIs of type {roi_type}")  # noqa: G004
                    continue

                # 1. build up the points for a layer.
                corners: list[list[list[int | FloatLike]]] = []
                shapes: list[str] = []
                for r in rois:  # type: ignore[assignment]
                    for (
                        q1,
                        q2,
                        q3,
                        q4,
                        is_center_slice,
                    ) in r.bounding_box.iter_z_slices_nonnegative():
                        corners.append(
                            [
                                [r.timepoint, r.channel, *_point_to_list(pt)]
                                for pt in [q1, q2, q3, q4]
                            ]
                        )
                        shapes.append("rectangle" if is_center_slice else "ellipse")
                logging.debug("Point count for ROI type %s: %d", r.typename, len(corners))

                # 2. Build up collection of layer parameters.
                params: dict[str, object] = {
                    # We need these parameters regardless of the ROI type
                    "name": roi_type.__name__,
                    "shape_type": shapes,
                    "face_color": "transparent",
                    COLOR_PARAMS_KEY: layer_color,
                }

                features: dict[str, Sized] = {}
                format_string_parts: list[str] = []

                # 3. Add text if necessary based on ROI type.
                # Add the merge index for merge input or output record.
                # Add the trace ID whenever > 1 ROI is in the same trace.
                if roi_type in [MergeContributorRoi, MergedRoi, SingletonRoi]:
                    if roi_type in [MergeContributorRoi, MergedRoi]:
                        features.update(
                            {
                                "mergeId": [
                                    r.id if roi_type == MergedRoi else r.merge_index
                                    for r in rois
                                    for _ in r.bounding_box.iter_z_slices_nonnegative()
                                ]
                            }
                        )
                        # NB: this is more like "ID after merge step", so it applies
                        # even to the singleton ROIs.
                        format_string_parts.append("i={mergeId}")
                    if roi_type in [MergedRoi, SingletonRoi]:
                        logging.debug(
                            "Adding trace IDs to display for ROIs of type: %s", roi_type.__name__
                        )
                        features.update(
                            {
                                "traceId": [
                                    r.traceId.get  # type: ignore[attr-defined]
                                    for r in rois
                                    for _ in r.bounding_box.iter_z_slices_nonnegative()
                                ]
                            }
                        )
                        format_string_parts.append("t={traceId}")
                    if roi_type == SingletonRoi:
                        if display_roi_id_for_singletons():
                            logging.debug(
                                "Adding ROI ID to display for ROIs of type: %s", roi_type.__name__
                            )
                            features.update(
                                {
                                    "roiId": [
                                        r.id
                                        for r in rois
                                        for _ in r.bounding_box.iter_z_slices_nonnegative()
                                    ]
                                }
                            )
                            # NB: this ROI set is disjoint with other which generates a i=... format string
                            format_string_parts.append("i={roiId}")
                        else:
                            logging.debug(
                                "Skipping addition of ROI IDs for ROIs of type: %s",
                                roi_type.__name__,
                            )
                elif roi_type == ProximityRejectedRoi:
                    match get_maximum_number_of_proximity_partners_to_display():
                        case 0:
                            logging.debug(
                                "Skipping annotation for ROIs of type: %s", roi_type.__name__
                            )
                        case int(max_neighbors):
                            logging.debug(
                                "Adding annotation for ROIs of type: %s", roi_type.__name__
                            )
                            features = {
                                "proximityAnnotation": [
                                    f"{r.id}: {_get_proximity_rejects_neighbors_text(r, limit=max_neighbors)}"  # type: ignore[arg-type]
                                    for r in rois
                                    for _ in r.bounding_box.iter_z_slices_nonnegative()
                                ]
                            }
                            format_string_parts.append("{proximityAnnotation}")
                        case x:
                            raise TypeError(
                                f"Expected an integer for maximum number of proximity partners to display, but got {type(x).__name__}"
                            )

                if features:
                    if not format_string_parts:
                        raise RuntimeError("Features is nonempty but format string parts is empty")
                    text_properties: dict[str, object] = {
                        "string": ", ".join(format_string_parts),
                        "size": TEXT_SIZE,
                        "color": layer_color,
                    }
                    params.update({"features": features, "text": text_properties})
                    logging.debug(
                        "Feature counts: %s",
                        ", ".join(f"{k} -> {len(vs)}" for k, vs in features.items()),
                    )

                # 4. Add the layer to the growing collection.
                layers.append((corners, params, "shapes"))

        return layers

    return build_layers


def _get_proximity_rejects_neighbors_text(roi: ProximityRejectedRoi, *, limit: int) -> str:
    neighbors: list[RoiId] = sorted(roi.neighbors)[:limit]
    sep: str = ","
    extra: int = len(roi.neighbors) - len(neighbors)
    return sep.join(map(str, neighbors)) + (f"{sep}+{extra}" if extra > 0 else "")


@doc(
    summary="Determine if the given path may be an input file to parse.",
    parameters=dict(path="Path to test as a plausible input file"),
    returns="The result of the compound test",
)
def _is_plausible_input_file(path: Path) -> bool:
    return path.is_file() and path.suffix == ".csv" and path.name.split(".")[0].endswith("_rois")


def _parse_non_contributor_non_proximal_rois(
    path: Path,
) -> list[NonNuclearRoi | SingletonRoi | MergedRoi]:
    rois: list[NonNuclearRoi | SingletonRoi | MergedRoi] = []
    try:
        data = pd.read_csv(path)
    except EmptyDataError:
        logging.warning("Empty data file: %s", path)
        return []
    for _, row in data.iterrows():
        roiId, time, channel, box, traceId, trace_partners, maybe_nuc_num, maybe_id_and_contribs = (
            _parse_nucleus_labeled_record(row)
        )
        roi: NonNuclearRoi | SingletonRoi | MergedRoi
        match (maybe_nuc_num, maybe_id_and_contribs):
            case (None, _):
                roi = NonNuclearRoi(timepoint=time, channel=channel, bounding_box=box)
            case (nuc_num, None):
                roi = SingletonRoi(
                    id=roiId,
                    timepoint=time,
                    channel=channel,
                    bounding_box=box,
                    traceId=traceId,
                    trace_partners=trace_partners,
                    nucleus_number=nuc_num,  # type: ignore[arg-type]
                )
            case (nuc_num, (main_id, contrib_ids)):
                roi = MergedRoi(
                    id=main_id,  # type: ignore[arg-type]
                    timepoint=time,
                    channel=channel,
                    bounding_box=box,
                    nucleus_number=nuc_num,  # type: ignore[arg-type]
                    traceId=traceId,
                    trace_partners=trace_partners,
                    contributors=contrib_ids,  # type: ignore[arg-type]
                )
            case _:
                raise Exception(  # noqa: TRY002
                    f"Could not determine how to build ROI! maybe_nuc_num={maybe_nuc_num}, maybe_id_and_contribs={maybe_id_and_contribs}"
                )
        rois.append(roi)
    return rois


@doc(
    summary="Read the data from the given file and parse it into bounding boxes.",
    parameters=dict(path="Path to data file from which to parse bounding boxes"),
    returns="List of tuples of ID, neighbors, time, channel, and bounding box.",
)
def _parse_proximity_rejects(
    path: Path,
) -> list[tuple[RoiId, set[RoiId], Timepoint, Channel, BoundingBox3D]]:
    try:
        spot_data = pd.read_csv(path, index_col=None)
    except EmptyDataError:
        logging.warning("Empty data file: %s", path)
        return []
    return _parse_proximity_rejects_table(spot_data)


def _parse_proximity_rejects_table(
    rois: pd.DataFrame,
) -> list[tuple[RoiId, set[RoiId], Timepoint, Channel, BoundingBox3D]]:
    return [
        (
            record[ROI_ID_COLUMN],
            _parse_neighbors(str(record[TOO_CLOSE_ROIS_COLUMN])),
            *_parse_time_channel_box_trio(record),
        )
        for _, record in rois.iterrows()
    ]


def _parse_neighbors(raw_value: str) -> set[RoiId]:
    values = list(map(int, raw_value.split(" ")))
    unique = set(values)
    if len(unique) == len(values):
        return unique
    raise ValueError(f"Repeated values are present among proximal neighbors: {values}")


def _parse_merge_contributor_record(
    record: pd.Series,  # type: ignore[type-arg]
) -> MergeContributorRoi:
    record: dict[str, int | FloatLike] = record.to_dict()  # type: ignore[no-redef]
    index: RoiId = record[ROI_ID_COLUMN]
    merge_column_name = "mergeOutput"
    raw_merge_index = record[merge_column_name]
    MergeIdType: TypeAlias = RoiId
    merge_index: MergeIdType
    if isinstance(raw_merge_index, MergeIdType):
        merge_index = raw_merge_index
    elif isinstance(raw_merge_index, str):
        merge_index = MergeIdType(raw_merge_index)
    else:
        raise TypeError(
            f"Got {type(raw_merge_index)}, not str or {MergeIdType.__name__}, from '{merge_column_name}': {raw_merge_index}"
        )
    time, channel, box = _parse_time_channel_box_trio(record)
    return MergeContributorRoi(
        id=index, timepoint=time, channel=channel, bounding_box=box, merge_index=merge_index
    )


def _parse_nucleus_labeled_record(
    record: pd.Series,  # type: ignore[type-arg]
) -> tuple[
    RoiId,
    Timepoint,
    Channel,
    BoundingBox3D,
    TraceIdFrom0,
    set[RoiId],
    Optional[NucleusNumber],
    Optional[IdAndContributors],
]:
    record: dict[str, int | FloatLike] = record.to_dict()  # type: ignore[no-redef]

    roiId: RoiId = record[ROI_ID_COLUMN]
    traceId: TraceIdFrom0 = TraceIdFrom0(record["traceId"])
    trace_partners: set[RoiId] = _parse_roi_ids_field(record, key="tracePartners")

    raw_nuc_num: int = record["nucleusNumber"]
    maybe_nuc_num: Optional[NucleusNumber] = (
        None if raw_nuc_num == 0 else NucleusNumber(raw_nuc_num)
    )

    merge_column_name = "mergePartners"
    id_and_contribs: Optional[IdAndContributors]
    raw_merge_indices = record[merge_column_name]
    if raw_merge_indices is None or raw_merge_indices == "" or pd.isna(raw_merge_indices):
        id_and_contribs = None
    else:
        roi_id: RoiId = record[ROI_ID_COLUMN]
        contribs = _parse_roi_ids_field(record, key=merge_column_name)
        id_and_contribs = (roi_id, contribs)

    time, channel, box = _parse_time_channel_box_trio(record)

    return roiId, time, channel, box, traceId, trace_partners, maybe_nuc_num, id_and_contribs


def _parse_roi_ids_field(
    row: pd.Series,  # type: ignore[type-arg]
    *,
    key: str,
    intra_field_delimiter: str = " ",
) -> set[RoiId]:
    raw_value: object = row[key]
    result: set[RoiId]
    if isinstance(raw_value, int):
        result = {raw_value}
    elif isinstance(raw_value, str):
        result = set(map(int, raw_value.split(intra_field_delimiter)))
    elif pd.isna(raw_value):  # type: ignore[call-overload]
        result = set()
    else:
        raise TypeError(f"Got {type(raw_value)}, not str or int, from '{key}': {raw_value}")
    return result


def _parse_time_channel_box_trio(
    record: dict[str, int | FloatLike] | pd.Series,  # type: ignore[type-arg]
) -> tuple[Timepoint, Channel, BoundingBox3D]:
    record: dict[str, int | FloatLike] = (  # type: ignore[no-redef]
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
    return time, channel, box  # type: ignore[return-value]


@doc(
    summary="Flatten point coordinates to list",
    parameters=dict(pt="Point to flatten"),
    returns="[z, y, x]",
)
def _point_to_list(pt: Point3D) -> list[FloatLike]:
    return [pt.z, pt.y, pt.x]
