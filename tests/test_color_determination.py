import pytest

from looptrace_regionals_vis.colors import INDIGO, PALE_RED_CLAY, PALE_SKY_BLUE
from looptrace_regionals_vis.processing import ProcessingStatus


@pytest.mark.parametrize(
    ("status", "expected_color"),
    [
        (ProcessingStatus.Unfiltered, INDIGO),
        (ProcessingStatus.ProximityFiltered, PALE_SKY_BLUE),
        (ProcessingStatus.ProximityAndNucleiFiltered, PALE_RED_CLAY),
    ],
)
def test_colors_are_as_expected(status, expected_color):
    observed_color = status.color
    assert (
        observed_color == expected_color
    ), f"Color for data processing status {status} wasn't as expected ({expected_color}): {observed_color}"


@pytest.mark.parametrize("status", list(ProcessingStatus))
def test_each_member_of_data_status_enum_resolves_to_a_color(status):
    assert status.color is not None, f"Got null color for data processing status {status}"
