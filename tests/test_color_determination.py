import pytest
import hypothesis as hyp
from hypothesis import strategies as st

from looptrace_regionals_vis.colors import INDIGO, PALE_RED_CLAY, PALE_SKY_BLUE
from looptrace_regionals_vis.processing import ProcessingStatus
from looptrace_regionals_vis.reader import get_data_color


@pytest.mark.parametrize(
    ("status", "expected_color"),
    [
        (ProcessingStatus.Unfiltered, INDIGO),
        (ProcessingStatus.ProximityOnly, PALE_SKY_BLUE),
        (ProcessingStatus.ProximityAndNuclei, PALE_RED_CLAY),
    ],
)
def test_colors_are_as_expected(status, expected_color):
    observed_color = get_data_color(status)
    assert (
        observed_color == expected_color
    ), f"Color for data processing status {status} wasn't as expected ({expected_color}): {observed_color}"


@pytest.mark.parametrize("status", [s for s in ProcessingStatus])
def test_each_member_of_data_status_enum_resolves_to_a_color(status):
    assert get_data_color(status) is not None, f"Got null color for data processing status {status}"


@hyp.given(
    status=st.one_of(
        st.sampled_from(
            tuple(m.name for m in ProcessingStatus)
        ),  # need actual enum member, not the name
        st.integers(min_value=0, max_value=len(ProcessingStatus) - 1),
        st.text(),
    )
)
def test_illegal_argument_raises_expected_error(status):
    with pytest.raises(ValueError) as error_context:
        get_data_color(status)
    assert "Could not resolve color for data status!" in str(
        error_context.value
    ), "Expected error message portion doesn't appear in observed error message."
