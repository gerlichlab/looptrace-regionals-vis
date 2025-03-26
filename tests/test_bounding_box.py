"""Tests of the bounding box data type used to visualise regional spots"""

import dataclasses
from math import floor
from typing import Optional

import hypothesis as hyp
import pytest
from hypothesis import strategies as st

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
    zMin, zMax = min(z1, z2), max(z1, z2)
    yMin, yMax = min(y1, y2), max(y1, y2)
    xMin, xMax = min(x1, x2), max(x1, x2)
    zc = draw(st.floats(min_value=zMin, max_value=zMax))
    yc = draw(st.floats(min_value=yMin, max_value=yMax))
    xc = draw(st.floats(min_value=xMin, max_value=xMax))
    return BoundingBox3D(
        center=Point3D(z=zc, y=yc, x=xc),
        zMin=zMin,
        zMax=zMax,
        yMin=yMin,
        yMax=yMax,
        xMin=xMin,
        xMax=xMax,
    )


@st.composite
def gen_bbox_arguments_with_contextually_illegal_center(draw):
    """Set up a strategy such that at least one center will be outside the bounding box."""
    (z1, z2), (y1, y2), (x1, x2) = draw(st.tuples(gen_pair(), gen_pair(), gen_pair()))
    zc = draw(gen_legal_coordinate())
    yc = draw(gen_legal_coordinate())
    xc = draw(gen_legal_coordinate())
    zMin, zMax = min(z1, z2), max(z1, z2)
    yMin, yMax = min(y1, y2), max(y1, y2)
    xMin, xMax = min(x1, x2), max(x1, x2)

    # Gate on the condition that we've generated at least one problem, as desired.
    hyp.assume(zc < zMin or zc > zMax or yc < yMin or yc > yMax or xc < xMin or xc > xMax)

    return {
        "zc": zc,
        "yc": yc,
        "xc": xc,
        "zMin": zMin,
        "zMax": zMax,
        "yMin": yMin,
        "yMax": yMax,
        "xMin": xMin,
        "xMax": xMax,
    }


@st.composite
def gen_bbox_arguments_with_contextually_illegal_endpoints(draw):
    """Generate a valid bounding box, center valid w.r.t. box bounds."""
    (zMin, zMax), (yMin, yMax), (xMin, xMax) = draw(st.tuples(gen_pair(), gen_pair(), gen_pair()))

    # We want at least one such nonsense bounds.
    hyp.assume(zMin > zMax or yMin > yMax or xMin > xMax)

    zc = draw(st.floats(min_value=min(zMin, zMax), max_value=max(zMin, zMax)))
    yc = draw(st.floats(min_value=min(yMin, yMax), max_value=max(yMin, yMax)))
    xc = draw(st.floats(min_value=min(xMin, xMax), max_value=max(xMin, xMax)))

    return {
        "zc": zc,
        "yc": yc,
        "xc": xc,
        "zMin": zMin,
        "zMax": zMax,
        "yMin": yMin,
        "yMax": yMax,
        "xMin": xMin,
        "xMax": xMax,
    }


@hyp.given(box=gen_bbox_legit())
@pytest.mark.parametrize(
    ("api_member", "validation_attribute"),
    [
        ("get_zMin", "zMin"),
        ("get_zMax", "zMax"),
        ("get_yMin", "yMin"),
        ("get_yMax", "yMax"),
        ("get_xMin", "xMin"),
        ("get_xMax", "xMax"),
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
    with pytest.raises(
        ValueError, match="For each dimension, center coordinate must be within min/max bounds!"
    ):
        BoundingBox3D.from_flat_arguments(**error_inducing_arguments)


@hyp.given(error_inducing_arguments=gen_bbox_arguments_with_contextually_illegal_endpoints())
def test_endpoints_must_make_sense(error_inducing_arguments):
    with pytest.raises(ValueError, match="For each dimension, min must be no more than max!"):
        BoundingBox3D.from_flat_arguments(**error_inducing_arguments)


@hyp.given(box=gen_bbox_legit())
def test_diff_between_endpoints_is_nonnegative_for_all_dimensions(box, dimname):
    assert getattr(box, f"{dimname}Max") - getattr(box, f"{dimname}Min") >= 0


@hyp.given(box=gen_bbox_legit())
def test_diff_between_center_and_min_is_nonnegative_for_all_dimensions(box, dimname):
    assert getattr(box.center, dimname) - getattr(box, f"{dimname}Min") >= 0


@hyp.given(box=gen_bbox_legit())
def test_diff_between_max_and_center_is_nonnegative_for_all_dimensions(box, dimname):
    assert getattr(box, f"{dimname}Max") - getattr(box.center, dimname) >= 0


@hyp.given(box=gen_bbox_legit(min_z=-5, max_z=50))
@hyp.settings(max_examples=1000)  # Bump up example count here since the logic is tricky.
def test_iter_z_slices_nonnegative__always_designates_zero_or_one_z_slice_as_central(box):
    is_center_flags: list[bool] = [
        is_center for _, _, _, _, is_center in box.iter_z_slices_nonnegative()
    ]
    num_central_exp = 0 if round(box.center.z) < 0 or round(box.center.z) > box.get_zMax() else 1
    num_central_obs = sum(is_center_flags)
    assert (
        num_central_obs == num_central_exp
    ), f"Expected {num_central_exp} central slice(s) but got {num_central_obs}"


@hyp.given(box=gen_bbox_legit(min_z=-5, max_z=5))  # smaller z range here for efficiency
def test_iter_z_slices_nonnegative__maintains_box_coordinates(box):
    for i, (q1, q2, q3, q4, _) in enumerate(box.iter_z_slices_nonnegative()):
        assert (  # noqa: PT018
            q1.x == box.xMax and q1.y == box.yMin
        ), f"Bad top-left point ({q1}) in {i}-th z-slice, from box {box}"
        assert (  # noqa: PT018
            q2.x == box.xMin and q2.y == box.yMin
        ), f"Bad top-left point ({q2}) in {i}-th z-slice, from box {box}"
        assert (  # noqa: PT018
            q3.x == box.xMin and q3.y == box.yMax
        ), f"Bad top-left point ({q3}) in {i}-th z-slice, from box {box}"
        assert (  # noqa: PT018
            q4.x == box.xMax and q4.y == box.yMax
        ), f"Bad bottom-right point ({q4}) in {i}-th z-slice, from box {box}"


@hyp.given(box=gen_bbox_legit(min_z=-50, max_z=50))
def test_iter_z_slices_nonnegative__slice_count_is_always_one_greater_than_difference_between_max_of_z_floors_and_zero(
    box,
):
    """There's one slice produced for each nonnegative integer in [floor(zMin), floor(zMax))."""
    exp_num_slices = max(0, floor(box.zMax) + 1) - max(0, floor(box.zMin))
    obs_num_slices = sum(1 for _ in box.iter_z_slices_nonnegative())
    assert (
        obs_num_slices == exp_num_slices
    ), f"Expected {exp_num_slices} z-slices but got {obs_num_slices} from box {box}"


@hyp.given(box=gen_bbox_legit())
def test_z_slice_iteration_is_empty_if_and_only_if_both_z_endpoints_are_negative(box):
    if box.zMin < 0 and box.zMax < 0:
        with pytest.raises(StopIteration):
            next(box.iter_z_slices_nonnegative())
    else:
        try:
            next(box.iter_z_slices_nonnegative())
        except StopIteration:
            pytest.fail(f"Empty z-slice iteration from this bounding box: {box}")
