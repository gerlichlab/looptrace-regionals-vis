import pytest

from looptrace_regionals_vis.colors import IBM_BLUE, IBM_ORANGE, IBM_PINK, IBM_PURPLE, IBM_YELLOW
from looptrace_regionals_vis.reader import RoiType


@pytest.mark.parametrize(
    ("status", "expected_color"),
    [
        (RoiType.MergeContributor, IBM_BLUE),
        (RoiType.DiscardForProximity, IBM_PURPLE),
        (RoiType.AcceptedSingleton, IBM_PINK),
        (RoiType.DiscardForNonNuclearity, IBM_ORANGE),
        (RoiType.AcceptedMerger, IBM_YELLOW),
    ],
)
def test_colors_are_as_expected(status, expected_color):
    observed_color = status.color
    assert (
        observed_color == expected_color
    ), f"Color for data processing status {status} wasn't as expected ({expected_color}): {observed_color}"


@pytest.mark.parametrize("roi_type", list(RoiType))
def test_each_member_of_data_status_enum_resolves_to_a_color(roi_type):
    assert roi_type.color is not None, f"Got null color for data ROI type {roi_type}"
