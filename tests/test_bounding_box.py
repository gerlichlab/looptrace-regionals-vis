"""Tests of the bounding box data type used to visualise regional spots"""

import dataclasses
from math import floor
from typing import Optional

import hypothesis as hyp
from hypothesis import strategies as st
import pytest

from looptrace_regionals_vis.bounding_box import BoundingBox3D
from looptrace_regionals_vis.point import Point3D


def pytest_generate_tests(metafunc):
    if "dimname" in metafunc.fixturenames:
        metafunc.parametrize("dimname", [f.name for f in dataclasses.fields(Point3D)])


def gen_legal_coordinate(*, min_value: Optional[float] = None, max_value: Optional[float] = None):
    return st.floats(
        min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False
    )


def gen_pair(*, min_value: Optional[float] = None, max_value: Optional[float] = None):
    return st.tuples(
        gen_legal_coordinate(min_value=min_value, max_value=max_value),
        gen_legal_coordinate(min_value=min_value, max_value=max_value),
    )


@st.composite
def gen_bbox_legit(draw, *, min_z: Optional[float] = None, max_z: Optional[float] = None):
    """Generate a valid bounding box, center valid w.r.t. box bounds."""
    (z1, z2) = draw(gen_pair(min_value=min_z, max_value=max_z))
    (y1, y2), (x1, x2) = draw(st.tuples(gen_pair(), gen_pair()))
    z_min, z_max = min(z1, z2), max(z1, z2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    x_min, x_max = min(x1, x2), max(x1, x2)
    zc = draw(st.floats(min_value=z_min, max_value=z_max))
    yc = draw(st.floats(min_value=y_min, max_value=y_max))
    xc = draw(st.floats(min_value=x_min, max_value=x_max))
    return BoundingBox3D(
        center=Point3D(z=zc, y=yc, x=xc),
        z_min=z_min,
        z_max=z_max,
        y_min=y_min,
        y_max=y_max,
        x_min=x_min,
        x_max=x_max,
    )


@st.composite
def gen_bbox_arguments_with_contextually_illegal_center(draw):
    """Set up a strategy such that at least one center will be outside the bounding box."""
    (z1, z2), (y1, y2), (x1, x2) = draw(st.tuples(gen_pair(), gen_pair(), gen_pair()))
    zc = draw(gen_legal_coordinate())
    yc = draw(gen_legal_coordinate())
    xc = draw(gen_legal_coordinate())
    z_min, z_max = min(z1, z2), max(z1, z2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    x_min, x_max = min(x1, x2), max(x1, x2)

    # Gate on the condition that we've generated at least one problem, as desired.
    hyp.assume(zc < z_min or zc > z_max or yc < y_min or yc > y_max or xc < x_min or xc > x_max)

    return {
        "zc": zc,
        "yc": yc,
        "xc": xc,
        "z_min": z_min,
        "z_max": z_max,
        "y_min": y_min,
        "y_max": y_max,
        "x_min": x_min,
        "x_max": x_max,
    }


@st.composite
def gen_bbox_arguments_with_contextually_illegal_endpoints(draw):
    """Generate a valid bounding box, center valid w.r.t. box bounds."""
    (z_min, z_max), (y_min, y_max), (x_min, x_max) = draw(
        st.tuples(gen_pair(), gen_pair(), gen_pair())
    )

    # We want at least one such nonsense bounds.
    hyp.assume(z_min > z_max or y_min > y_max or x_min > x_max)

    zc = draw(st.floats(min_value=min(z_min, z_max), max_value=max(z_min, z_max)))
    yc = draw(st.floats(min_value=min(y_min, y_max), max_value=max(y_min, y_max)))
    xc = draw(st.floats(min_value=min(x_min, x_max), max_value=max(x_min, x_max)))

    return {
        "zc": zc,
        "yc": yc,
        "xc": xc,
        "z_min": z_min,
        "z_max": z_max,
        "y_min": y_min,
        "y_max": y_max,
        "x_min": x_min,
        "x_max": x_max,
    }


@hyp.given(box=gen_bbox_legit())
@pytest.mark.parametrize(
    ("api_member", "validation_attribute"),
    [
        ("get_z_min", "z_min"),
        ("get_z_max", "z_max"),
        ("get_y_min", "y_min"),
        ("get_y_max", "y_max"),
        ("get_x_min", "x_min"),
        ("get_x_max", "x_max"),
    ],
)
def test_rectangle_protocol_support(box, api_member, validation_attribute):
    get = getattr(box, api_member)
    obs = get()
    exp = getattr(box, validation_attribute)
    assert (
        obs == exp
    ), f"Expected {exp} (from .{validation_attribute}) but got {obs} (from .{api_member}())"


@hyp.given(error_inducing_arguments=gen_bbox_arguments_with_contextually_illegal_center())
def test_center_must_be_within_bounds(error_inducing_arguments):
    with pytest.raises(ValueError) as error_context:
        return BoundingBox3D.from_flat_arguments(**error_inducing_arguments)
    exp_msg = "For each dimension, center coordinate must be within min/max bounds!"
    obs_msg = str(error_context.value)
    assert obs_msg == exp_msg, f"Expected error message '{exp_msg}' but got '{obs_msg}'"


@hyp.given(error_inducing_arguments=gen_bbox_arguments_with_contextually_illegal_endpoints())
def test_endpoints_must_make_sense(error_inducing_arguments):
    with pytest.raises(ValueError) as error_context:
        return BoundingBox3D.from_flat_arguments(**error_inducing_arguments)
    exp_msg = "For each dimension, min must be no more than max!"
    obs_msg = str(error_context.value)
    assert obs_msg == exp_msg, f"Expected error message '{exp_msg}' but got '{obs_msg}'"


@hyp.given(box=gen_bbox_legit())
def test_diff_between_endpoints_is_nonnegative_for_all_dimensions(box, dimname):
    assert getattr(box, f"{dimname}_max") - getattr(box, f"{dimname}_min") >= 0


@hyp.given(box=gen_bbox_legit())
def test_diff_between_center_and_min_is_nonnegative_for_all_dimensions(box, dimname):
    assert getattr(box.center, dimname) - getattr(box, f"{dimname}_min") >= 0


@hyp.given(box=gen_bbox_legit())
def test_diff_between_max_and_center_is_nonnegative_for_all_dimensions(box, dimname):
    assert getattr(box, f"{dimname}_max") - getattr(box.center, dimname) >= 0


@hyp.given(box=gen_bbox_legit(min_z=-50, max_z=50))
@hyp.settings(max_examples=1000)  # Bump up example count here since the logic is tricky.
def test_iter_z_slices__always_designates_zero_or_one_z_slice_as_central(box):
    is_center_flags: list[bool] = [is_center for _, _, _, _, is_center in box.iter_z_slices()]
    num_central_exp = 0 if round(box.center.z) > box.get_z_max() else 1
    num_central_obs = sum(is_center_flags)
    assert (
        num_central_obs == num_central_exp
    ), f"Expected {num_central_exp} central slice(s) but got {num_central_obs}"


@hyp.given(box=gen_bbox_legit(min_z=-5, max_z=5))  # smaller z range here for efficiency
def test_iter_z_slices__maintains_box_coordinates(box):
    for i, (q1, q2, q3, q4, _) in enumerate(box.iter_z_slices()):
        assert (
            q1.x == box.x_max and q1.y == box.y_min
        ), f"Bad top-left point ({q1}) in {i}-th z-slice, from box {box}"
        assert (
            q2.x == box.x_min and q2.y == box.y_min
        ), f"Bad top-left point ({q2}) in {i}-th z-slice, from box {box}"
        assert (
            q3.x == box.x_min and q3.y == box.y_max
        ), f"Bad top-left point ({q3}) in {i}-th z-slice, from box {box}"
        assert (
            q4.x == box.x_max and q4.y == box.y_max
        ), f"Bad bottom-right point ({q4}) in {i}-th z-slice, from box {box}"


@hyp.given(box=gen_bbox_legit(min_z=-50, max_z=50))
def test_iter_z_slices__slice_count_is_always_one_greater_than_difference_between_z_floors(box):
    exp_num_slices = floor(box.z_max) - floor(box.z_min) + 1
    obs_num_slices = sum(1 for _ in box.iter_z_slices())
    assert (
        obs_num_slices == exp_num_slices
    ), f"Expected {exp_num_slices} z-slices but got {obs_num_slices} from box {box}"
