"""Tests for points in Euclidean space"""

import math

import hypothesis as hyp
from hypothesis import strategies as st
import pytest

from looptrace_regionals_vis.point import Point3D


legal_float = st.floats(allow_nan=False, allow_infinity=False)
gen_int_or_float = st.one_of(st.integers(), legal_float)
gen_infinity = st.sampled_from((-math.inf, math.inf))


@hyp.given(coordinates=st.tuples(legal_float, legal_float, legal_float))
def test_point_construction_is_keyword_only(coordinates):
    z, y, x = coordinates
    Point3D(z=z, y=y, x=x)  # 'control'/pretest should work.
    with pytest.raises(TypeError) as error_context:  # 'experiment' should trigger error.
        Point3D(z, y, x)
    expected_submessage = "takes 1 positional argument but 4 were given"
    observed_message = str(error_context.value)
    assert (
        expected_submessage in observed_message
    ), f"Did not find expected submessage ('{expected_submessage}') in error message ('{observed_message}')"


@hyp.given(
    coordinates=st.tuples(gen_int_or_float, gen_int_or_float, gen_int_or_float).filter(
        lambda coords: not all(isinstance(c, float) for c in coords)
    )
)
def test_point_cannot_be_constructed_with_non_float(coordinates):
    z, y, x = coordinates
    with pytest.raises(TypeError) as error_context:
        Point3D(z=z, y=y, x=x)
    assert str(error_context.value).startswith(
        "Value of each field of point must be floating-point"
    )


@hyp.given(
    coordinates=st.tuples(
        st.one_of(legal_float, gen_infinity),
        st.one_of(legal_float, gen_infinity),
        st.one_of(legal_float, gen_infinity),
    ).filter(
        lambda coords: any(math.isinf(c) for c in coords) and not any(math.isnan(c) for c in coords)
    )
)
def test_point_cannot_be_constructed_with_infinite(coordinates):
    z, y, x = coordinates
    with pytest.raises(ValueError) as error_context:
        Point3D(z=z, y=y, x=x)
    assert "Cannot use an infinite value as a point coordinate!" == str(error_context.value)


@hyp.given(
    coordinates=st.tuples(
        st.one_of(legal_float, st.just(math.nan)),
        st.one_of(legal_float, st.just(math.nan)),
        st.one_of(legal_float, st.just(math.nan)),
    ).filter(
        lambda coords: any(math.isnan(c) for c in coords) and not any(math.isinf(c) for c in coords)
    )
)
def test_point_cannot_be_constructed_with_nan(coordinates):
    z, y, x = coordinates
    with pytest.raises(ValueError) as error_context:
        Point3D(z=z, y=y, x=x)
    assert "Cannot use a null numeric as a point coordinate!" == str(error_context.value)
