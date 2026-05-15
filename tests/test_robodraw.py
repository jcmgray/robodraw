import random

import pytest

from robodraw import Drawing
from robodraw.schematic import convex_hull_2d


def test_drawing_create():
    d = Drawing()
    assert isinstance(d, Drawing)


def _signed_area(poly):
    """Twice the signed area of a polygon (positive => counter-clockwise)."""
    n = len(poly)
    return sum(
        poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
        for i in range(n)
    )


def test_convex_hull_square_with_interior_point():
    pts = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)]
    idx = convex_hull_2d(pts)
    # the interior point (index 4) must not be on the hull
    assert 4 not in idx
    assert sorted(idx) == [0, 1, 2, 3]


def test_convex_hull_counter_clockwise():
    pts = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)]
    idx = convex_hull_2d(pts)
    hull = [pts[i] for i in idx]
    assert _signed_area(hull) > 0


def test_convex_hull_excludes_collinear_edge_points():
    # midpoint of the bottom edge (index 4) is collinear -> excluded
    pts = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 0)]
    idx = convex_hull_2d(pts)
    assert 4 not in idx
    assert sorted(idx) == [0, 1, 2, 3]


def test_convex_hull_matches_scipy():
    scipy_spatial = pytest.importorskip("scipy.spatial")

    rng = random.Random(42)
    for _ in range(5):
        pts = [(rng.uniform(-10, 10), rng.uniform(-10, 10)) for _ in range(40)]

        ours = {tuple(pts[i]) for i in convex_hull_2d(pts)}

        hull = scipy_spatial.ConvexHull(pts)
        theirs = {tuple(pts[i]) for i in hull.vertices}

        assert ours == theirs


def test_patch_around_runs_without_scipy():
    d = Drawing()
    n_before = len(d.ax.patches)
    # several points + radius -> > 3 expanded points -> exercises the hull path
    d.patch_around(
        [(0, 0), (3, 0), (3, 3), (0, 3), (1, 1)],
        radius=0.5,
    )
    assert len(d.ax.patches) > n_before
