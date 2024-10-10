"""Validation of what this plugin will or will not attempt to parse"""

import itertools
import shutil
from pathlib import Path

import pytest

from looptrace_regionals_vis import get_package_examples_folder, list_package_example_files
from looptrace_regionals_vis.reader import InputFileContentType, RoiType, get_reader

EXAMPLE_FILES: list[Path] = list_package_example_files()
ROI_TYPES_BY_FILE_TYPE: dict[InputFileContentType, set[RoiType]] = {
    InputFileContentType.MergeContributors: {RoiType.MergeContributor},
    InputFileContentType.ProximityRejects: {RoiType.DiscardForProximity},
    InputFileContentType.NucleiLabeled: {
        RoiType.AcceptedSingleton,
        RoiType.DiscardForNonNuclearity,
        RoiType.AcceptedMerger,
    },
}


def test_cannot_read_list_of_files():
    assert (
        get_reader(EXAMPLE_FILES) is None
    ), "Expected inability to parse list of filepaths, but got non-null reader!"


@pytest.mark.parametrize("wrap", [str, Path])
def test_would_read_collectivity_of_package_examples(wrap):
    folder = wrap(get_package_examples_folder())
    assert callable(
        get_reader(folder)
    ), f"Expected a callable reader for path {folder} but didn't get one!"


def test_path_which_is_not_extant_directory_cannot_be_parsed(tmp_path):
    assert get_reader(tmp_path / "P0001") is None


@pytest.mark.parametrize("wrap", [str, Path])
@pytest.mark.parametrize(
    "paths_to_mutate",
    [
        combo
        for k in range(1 + len(EXAMPLE_FILES))
        for combo in itertools.combinations(EXAMPLE_FILES, k)
    ],
)
def test_non_csv_files_are_skipped(tmp_path, wrap, paths_to_mutate):
    expected_roi_type_loss = sum(
        len(ROI_TYPES_BY_FILE_TYPE[ft])
        for ft in map(InputFileContentType.from_filepath, paths_to_mutate)
    )

    pairs_to_copy: list[tuple[Path, Path]] = []
    for src in EXAMPLE_FILES:
        fn = (src.with_suffix(".tsv") if src in paths_to_mutate else src).name
        pairs_to_copy.append((src, tmp_path / fn))
    for src, dst in pairs_to_copy:
        shutil.copy(src, dst)

    read_data = get_reader(wrap(tmp_path))
    layers = read_data(tmp_path)

    # Input data means every RoiType should be found.
    assert len(layers) == len(RoiType) - expected_roi_type_loss


@pytest.mark.parametrize("wrap", [str, Path])
def test_csv_with_unparsable_data_processing_status_is_skipped(tmp_path, wrap):
    for fp in EXAMPLE_FILES:
        shutil.copy(fp, tmp_path)
    (tmp_path / "P0001_rois.unfiltered.csv").touch()

    read_data = get_reader(wrap(tmp_path))
    layers = read_data(tmp_path)

    # Input data means every RoiType should be found.
    assert len(layers) == len(RoiType)


@pytest.mark.parametrize("wrap", [str, Path])
@pytest.mark.parametrize(
    ("filenames", "check_result"),
    [
        (
            ("P0001_rois.csv", "P0001_filler_rois.csv", "P0001.proximity_accepted.csv"),
            lambda r: r is None,
        ),
        (("P0001_rois.csv", "P0001.proximity_accepted.csv"), callable),
    ],
)
def test_repeated_data_processing_status_in_folder_to_read_prevents_parse(
    tmp_path, wrap, filenames, check_result
):
    for fn in filenames:
        (tmp_path / fn).touch()
    result = get_reader(wrap(tmp_path))
    assert check_result(result)
