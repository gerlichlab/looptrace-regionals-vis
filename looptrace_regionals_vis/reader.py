"""Tools for creating the reader of regional points data"""

import dataclasses
import logging
from collections import Counter
from collections.abc import Callable, Iterable
from enum import Enum
from pathlib import Path
from typing import Literal, Optional, TypeAlias

import pandas as pd
from numpydoc_decorator import doc  # type: ignore[import-untyped]

from .bounding_box import BoundingBox3D
from .point import FloatLike, Point3D
from .roi import MergeContributorRoi, MergedRoi, NonNuclearRoi, ProximityRejectedRoi, SingletonRoi
from .types import Channel, LayerParams, NucleusNumber, PathOrPaths, RoiId, Timepoint

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
SHAPE_PARAMS_KEY = "shape_type"
TEXT_SIZE = 8
TIME_COLUMN = "timepoint"


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
            if file_type == InputFileContentType.MergeContributors:
                rois_by_type = {
                    MergeContributorRoi: [
                        _parse_merge_contributor_record(row)
                        for _, row in pd.read_csv(file_path).iterrows()
                    ]
                }
            elif file_type == InputFileContentType.NucleiLabeled:
                rois_by_type = {}
                for roi in _parse_non_contributor_non_proximal_rois(file_path):
                    # Ignore type check here since we can't properly disambiguate the subcases
                    # w.r.t. ROI type.
                    rois_by_type.setdefault(type(roi), []).append(roi)  # type: ignore[arg-type]
            elif file_type == InputFileContentType.ProximityRejects:
                rois_by_type = {
                    ProximityRejectedRoi: [  # type: ignore[dict-item]
                        ProximityRejectedRoi(timepoint=t, channel=c, bounding_box=b)  # type: ignore[misc]
                        for t, c, b in parse_boxes(file_path)
                    ]
                }
            else:
                raise RuntimeError(f"Unexpected file type (can't determine ROI type)! {file_type}")

            for roi_type, rois in rois_by_type.items():
                get_text_color: Callable[[], str] = lambda: rois[0].color  # noqa: B023
                corners: list[list[list[int | FloatLike]]] = []
                shapes: list[str] = []
                for roi in rois:  # type: ignore[assignment]
                    for (
                        q1,
                        q2,
                        q3,
                        q4,
                        is_center_slice,
                    ) in roi.bounding_box.iter_z_slices_nonnegative():
                        corners.append(
                            [
                                [roi.timepoint, roi.channel, *_point_to_list(pt)]
                                for pt in [q1, q2, q3, q4]
                            ]
                        )
                        shapes.append("rectangle" if is_center_slice else "ellipse")
                logging.debug("Point count for ROI type %s: %d", roi.typename, len(shapes))
                params: dict[str, object] = {
                    "name": roi.typename,
                    "shape_type": shapes,
                    "face_color": "transparent",
                    COLOR_PARAMS_KEY: roi.color,
                }
                if roi_type in [MergeContributorRoi, MergedRoi]:
                    format_string: str
                    features: dict[str, object] = {}
                    ids, labels = zip(
                        *[
                            (roi_id, roi_text)
                            for roi in rois
                            for roi_id, roi_text in _create_roi_id_text_pairs(roi)
                        ],
                        strict=False,
                    )
                    if roi_type == MergeContributorRoi:
                        format_string = "{id} --> {merged_outputs}"
                        features = {"id": ids, "merged_outputs": labels}
                    elif roi_type == MergedRoi:
                        format_string = "{id} <-- {contributors}"
                        features = {"id": ids, "contributors": labels}
                    else:
                        raise RuntimeError(
                            f"Could not determine how to build text for ROI layer of type {roi_type}"
                        )
                    text_properties: dict[str, object] = {
                        "string": format_string,
                        "size": TEXT_SIZE,
                        "color": get_text_color(),
                    }
                    params.update({"features": features, "text": text_properties})
                layers.append((corners, params, "shapes"))

        return layers

    return build_layers


def _create_roi_id_text_pairs(roi: MergeContributorRoi | MergedRoi) -> Iterable[tuple[RoiId, str]]:
    text: str
    if isinstance(roi, MergeContributorRoi):
        text = str(roi.merge_index)
    elif isinstance(roi, MergedRoi):
        text = ";".join(map(str, sorted(roi.contributors)))
    else:
        raise TypeError(f"Cannot create ROI IDs text for value of type {type(roi).__name__}")
    for _ in roi.bounding_box.iter_z_slices_nonnegative():
        yield roi.id, text


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
    for _, row in pd.read_csv(path).iterrows():
        time, channel, box, maybe_nuc_num, maybe_id_and_contribs = _parse_nucleus_labeled_record(
            row
        )
        roi: NonNuclearRoi | SingletonRoi | MergedRoi
        match (maybe_nuc_num, maybe_id_and_contribs):
            case (None, _):
                roi = NonNuclearRoi(timepoint=time, channel=channel, bounding_box=box)
            case (nuc_num, None):
                roi = SingletonRoi(
                    timepoint=time,
                    channel=channel,
                    bounding_box=box,
                    nucleus_number=nuc_num,  # type: ignore[arg-type]
                )
            case (nuc_num, (main_id, contrib_ids)):
                roi = MergedRoi(
                    id=main_id,  # type: ignore[arg-type]
                    timepoint=time,
                    channel=channel,
                    bounding_box=box,
                    nucleus_number=nuc_num,  # type: ignore[arg-type]
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
    returns="List of tuples of time, channel, and box.",
)
def parse_boxes(  # noqa: D103
    path: Path,
) -> list[tuple[Timepoint, Channel, BoundingBox3D]]:
    box_cols = [f.name for f in dataclasses.fields(BoundingBox3D) if f.name != "center"]
    spot_data = pd.read_csv(
        path, usecols=BOX_CENTER_COLUMN_NAMES + box_cols + [TIME_COLUMN, CHANNEL_COLUMN]
    )
    time_channel_location_trios: list[tuple[Timepoint, Channel, BoundingBox3D]] = [
        _parse_time_channel_box_trio(record) for _, record in spot_data.iterrows()
    ]
    return time_channel_location_trios


def _parse_merge_contributor_record(
    record: pd.Series,  # type: ignore[type-arg]
) -> MergeContributorRoi:
    record: dict[str, int | FloatLike] = record.to_dict()  # type: ignore[no-redef]
    index: RoiId = record["index"]
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
) -> tuple[Timepoint, Channel, BoundingBox3D, Optional[NucleusNumber], Optional[IdAndContributors]]:
    record: dict[str, int | FloatLike] = record.to_dict()  # type: ignore[no-redef]
    raw_nuc_num: int = record["nucleusNumber"]
    maybe_nuc_num: Optional[NucleusNumber] = (
        None if raw_nuc_num == 0 else NucleusNumber(raw_nuc_num)
    )
    merge_column_name = "mergePartners"
    raw_merge_indices: object = record[merge_column_name]
    id_and_contribs: Optional[IdAndContributors]
    if raw_merge_indices is None or pd.isna(raw_merge_indices):  # type: ignore[call-overload]
        id_and_contribs = None
    else:
        roi_id: RoiId = record["index"]
        contribs: set[RoiId]
        if isinstance(raw_merge_indices, RoiId):
            contribs = {raw_merge_indices}
        elif isinstance(raw_merge_indices, str):
            contribs = {int(i) for i in raw_merge_indices.split(";")}
        else:
            raise TypeError(
                f"Got {type(raw_merge_indices)}, not str or int, from '{merge_column_name}': {raw_merge_indices}"
            )
        id_and_contribs = (roi_id, contribs)
    time, channel, box = _parse_time_channel_box_trio(record)
    return time, channel, box, maybe_nuc_num, id_and_contribs


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
