"""Tests for the parsing of data and building of layers"""

import pytest

from looptrace_regionals_vis import get_package_examples_folder
from looptrace_regionals_vis.colors import IBM_BLUE, IBM_ORANGE, IBM_PINK, IBM_PURPLE, IBM_YELLOW
from looptrace_regionals_vis.reader import COLOR_PARAMS_KEY, LayerParams, get_reader
from looptrace_regionals_vis.roi import (
    MergeContributorRoi,
    MergedRoi,
    NonNuclearRoi,
    ProximityRejectedRoi,
    SingletonRoi,
)


@pytest.mark.skip("not implemented")
def test_shapes_are_as_expected():
    pass


def test_colors_are_as_expected():
    # Input data means every ROI type should be found.
    exp_color_by_name = {
        MergeContributorRoi.__name__: IBM_PURPLE,
        ProximityRejectedRoi.__name__: IBM_BLUE,
        NonNuclearRoi.__name__: IBM_ORANGE,
        SingletonRoi.__name__: IBM_PINK,
        MergedRoi.__name__: IBM_YELLOW,
    }

    params: list[LayerParams] = determine_parameters(get_package_examples_folder())
    obs_color_by_name = {p["name"]: p[COLOR_PARAMS_KEY] for p in params}

    assert obs_color_by_name == exp_color_by_name


def determine_parameters(folder) -> list[LayerParams]:
    assert folder.is_dir(), f"Could not find example folder: {folder}"
    read = get_reader(folder)
    if not callable(read):
        raise RuntimeError(f"Expected to be able to read {folder} but couldn't!")  # noqa: TRY004
    try:
        layers = read(folder)
    except ValueError as e:
        raise RuntimeError("Expected successful data parse but didn't get it!") from e
    return [params for _, params, _ in layers]
