"""Tests for the projection and z-order math.

These are pure functions of the geometry, so we can assert exact /
sanity-checked values without rendering anything.
"""

import pytest

from robodraw import Drawing
from robodraw.schematic import (
    axonometric_project,
    coo_to_zorder,
    orthographic_project,
    orthographic_zorder,
    parse_projection,
)


def test_parse_projection_strings():
    assert parse_projection("orthographic") == ("orthographic", 20, 40)
    assert parse_projection("axonometric") == ("axonometric", 15, 120)
    assert parse_projection("isometric") == ("axonometric", 30, 150)


def test_parse_projection_tuples():
    # bare 2-tuple defaults to orthographic
    assert parse_projection((20, 40)) == ("orthographic", 20, 40)
    # explicit 3-tuple passes through
    assert parse_projection(("axonometric", 30, 150)) == (
        "axonometric",
        30,
        150,
    )


def test_parse_projection_unknown_raises():
    with pytest.raises(ValueError):
        parse_projection("perspective")
    with pytest.raises(ValueError):
        parse_projection(("bogus", 1, 2))


def test_projections_map_origin_to_origin():
    assert orthographic_project(0, 0, 0) == pytest.approx((0.0, 0.0))
    assert axonometric_project(0, 0, 0) == pytest.approx((0.0, 0.0))


def test_orthographic_topdown_collapses_z():
    # elevation=90 -> looking straight down; z must not affect screen pos
    x0, y0 = orthographic_project(1.0, 2.0, 0.0, azimuth=0, elevation=90)
    x1, y1 = orthographic_project(1.0, 2.0, 5.0, azimuth=0, elevation=90)
    assert (x0, y0) == pytest.approx((x1, y1))
    # and (azimuth=0, elevation=90) is exactly x-right, y-up
    assert (x0, y0) == pytest.approx((1.0, 2.0))


def test_scale_factors_applied():
    x, y = orthographic_project(
        1.0, 0.0, 0.0, azimuth=0, elevation=0, xscale=3.0
    )
    assert x == pytest.approx(3.0)


def test_zorder_monotone_towards_camera():
    # with a positive elevation, increasing z moves towards the camera
    z_lo = orthographic_zorder(0, 0, 0, azimuth=20, elevation=40)
    z_hi = orthographic_zorder(0, 0, 1, azimuth=20, elevation=40)
    assert z_hi > z_lo

    # axonometric: moving along +x should change depth monotonically
    a_lo = coo_to_zorder(0, 0, 0)
    a_hi = coo_to_zorder(1, 0, 0)
    assert a_hi != a_lo


def test_drawing_project_matches_module_function():
    d = Drawing(projection=("orthographic", 20, 40))
    got = d._3d_project(1.0, 2.0, 3.0)
    expected = orthographic_project(1.0, 2.0, 3.0, azimuth=20, elevation=40)
    assert got == pytest.approx(expected)

    d2 = Drawing(projection="isometric")
    got2 = d2._3d_project(1.0, 2.0, 3.0)
    expected2 = axonometric_project(1.0, 2.0, 3.0, a=30, b=150)
    assert got2 == pytest.approx(expected2)
