"""Tests for the parsing of data and building of layers"""

import importlib.resources
from pathlib import Path

import pytest

import looptrace_regionals_vis
from looptrace_regionals_vis.colors import INDIGO, PALE_RED_CLAY, PALE_SKY_BLUE
from looptrace_regionals_vis.reader import COLOR_PARAMS_KEY, SHAPE_PARAMS_KEY, LayerParams, get_reader, parse_boxes


def get_examples_path() -> Path:
    return importlib.resources.files(looptrace_regionals_vis).joinpath("examples")


@pytest.mark.parametrize("example_filename", [
    "P0001_rois.csv", 
    "P0001_rois.proximity_labeled.csv", 
    "P0001_rois.proximity_filtered.nuclei_labeled.csv"
])
def test_shapes_are_as_expected(example_filename):
    filepath = get_examples_path() / example_filename
    boxes = parse_boxes(filepath)
    expected_shapes = [
        "rectangle" if is_center else "ellipse" 
        for box in boxes 
        for _, _, is_center in box.iter_z_slices()
    ]
    layer_params = determine_parameters(filepath)
    try:
        observed_shapes = layer_params[SHAPE_PARAMS_KEY]
    except KeyError as e:
        raise AssertionError(
            f"Could not extract shapes from layer params ({layer_params}) after reading data from file {filepath}"
        ) from e
    assert observed_shapes == expected_shapes


@pytest.mark.parametrize(
    ("example_filename", "expected_color"),
    [
        ("P0001_rois.csv", INDIGO),
        ("P0001_rois.proximity_labeled.csv", PALE_SKY_BLUE),
        ("P0001_rois.proximity_filtered.nuclei_labeled.csv", PALE_RED_CLAY),
    ],
)
def test_colors_are_as_expected(example_filename, expected_color):
    filepath = get_examples_path() / example_filename
    layer_params = determine_parameters(filepath)
    try:
        observed_color = layer_params[COLOR_PARAMS_KEY]
    except KeyError as e:
        raise AssertionError(
            f"Could not extract edge color from layer params ({layer_params}) after reading data from file {filepath}"
        ) from e
    assert (
        observed_color == expected_color
    ), f"Expected color {expected_color} but got {observed_color} for data from file {filepath}"


def determine_parameters(filepath) -> LayerParams:
    assert filepath.is_file(), f"Could not find example file: {filepath}"
    read = get_reader(filepath)
    if not callable(read):
        raise AssertionError(f"Expected to be able to read {filepath} but couldn't!")
    try:
        _, layer_params, _ = read(filepath)
    except ValueError as e:
        raise AssertionError("Expected successful data parse but didn't get it!") from e
    return layer_params
