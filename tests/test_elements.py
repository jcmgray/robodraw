"""Smoke + style + position tests for every public ``Drawing`` method.

Output is matplotlib artists, so rather than comparing images we assert:

- the call runs and adds the expected artist(s) to ``d.ax``;
- explicit style kwargs reach the underlying matplotlib artist;
- for the simple primitives, the artist geometry equals the projected
  input coordinate (exact, not pixel-based);
- the ``preset`` system applies and is overridden by explicit kwargs.
"""

import pytest
from matplotlib.colors import to_rgba

from robodraw import Drawing


def _n_artists(d):
    return len(d.ax.patches) + len(d.ax.lines) + len(d.ax.texts)


# (name, callable taking a Drawing) for everything that should add >=1 artist
ELEMENT_CALLS = {
    "circle": lambda d: d.circle((0, 0)),
    "dot": lambda d: d.dot((0, 0)),
    "wedge": lambda d: d.wedge((0, 0), 0, 90),
    "square": lambda d: d.square((0, 0)),
    "regular_polygon": lambda d: d.regular_polygon((0, 0), n=5),
    "star": lambda d: d.star((0, 0)),
    "cross": lambda d: d.cross((0, 0)),
    "marker": lambda d: d.marker((0, 0), marker="^"),
    "rectangle": lambda d: d.rectangle((0, 0), (2, 0)),
    "cube": lambda d: d.cube((0, 0, 0)),
    "tetrahedron": lambda d: d.tetrahedron((0, 0, 0)),
    "octahedron": lambda d: d.octahedron((0, 0, 0)),
    "dodecahedron": lambda d: d.dodecahedron((0, 0, 0)),
    "icosahedron": lambda d: d.icosahedron((0, 0, 0)),
    "line": lambda d: d.line((0, 0), (1, 1)),
    "curve": lambda d: d.curve([(0, 0), (1, 1), (2, 0)]),
    "zigzag": lambda d: d.zigzag((0, 0), (4, 0)),
    "arrowhead": lambda d: d.arrowhead((0, 0), (1, 0)),
    "line_offset": lambda d: d.line_offset((0, 0), (2, 0), 0.5),
    "bezier": lambda d: d.bezier([(0, 0), (0, 1), (1, 1), (1, 0)]),
    "shape": lambda d: d.shape([(0, 0), (1, 0), (1, 1)]),
    "patch": lambda d: d.patch([(0, 0), (1, 0), (1, 1), (0, 1)]),
    "patch_around": lambda d: d.patch_around(
        [(0, 0), (2, 0), (2, 2), (0, 2)], radius=0.3
    ),
    "patch_around_circles": lambda d: d.patch_around_circles(
        (0, 0), 1, (3, 0), 1
    ),
    "cup": lambda d: d.cup((0, 0), (2, 1)),
    "text": lambda d: d.text((0, 0), "hi"),
    "text_between": lambda d: d.text_between((0, 0), (2, 0), "hi"),
    "label_ax": lambda d: d.label_ax(0.5, 0.5, "hi"),
    "label_fig": lambda d: d.label_fig(0.5, 0.5, "hi"),
    "grid": lambda d: d.grid(),
}


@pytest.mark.parametrize("name", sorted(ELEMENT_CALLS))
def test_element_smoke_adds_artist(name, drawing):
    before = _n_artists(drawing)
    ELEMENT_CALLS[name](drawing)
    assert _n_artists(drawing) > before


def test_grid3d_smoke():
    d = Drawing()
    d.cube((0, 0, 0))  # establish 3D bounds so no warning
    before = _n_artists(d)
    d.grid3d()
    assert _n_artists(d) > before


# --------------------------------------------------------------------------- #
# exact geometry + style propagation for the simple primitives
# --------------------------------------------------------------------------- #


def test_circle_position_and_style(drawing):
    drawing.circle(
        (1.0, 2.0),
        facecolor="red",
        edgecolor="blue",
        linewidth=3,
        radius=0.5,
    )
    c = drawing.ax.patches[-1]
    assert tuple(c.center) == pytest.approx((1.0, 2.0))
    assert c.radius == pytest.approx(0.5)
    assert to_rgba(c.get_facecolor()) == to_rgba("red")
    assert to_rgba(c.get_edgecolor()) == to_rgba("blue")
    assert c.get_linewidth() == pytest.approx(3)


def test_circle_color_kwarg_maps_to_facecolor(drawing):
    drawing.circle((0, 0), color="green")
    assert to_rgba(drawing.ax.patches[-1].get_facecolor()) == to_rgba("green")


def test_circle_3d_position_matches_projection(drawing):
    coo = (1.0, 2.0, 3.0)
    expected = drawing._3d_project(*coo)
    drawing.circle(coo)
    assert tuple(drawing.ax.patches[-1].center) == pytest.approx(expected)


def test_line_endpoints_and_style(drawing):
    drawing.line((0.0, 0.0), (2.0, 3.0), color="green", linewidth=4)
    ln = drawing.ax.lines[-1]
    assert list(ln.get_xdata()) == pytest.approx([0.0, 2.0])
    assert list(ln.get_ydata()) == pytest.approx([0.0, 3.0])
    assert to_rgba(ln.get_color()) == to_rgba("green")
    assert ln.get_linewidth() == pytest.approx(4)


def test_text_content_and_position(drawing):
    drawing.text((1.0, 2.0), "hello", color="purple", fontsize=20)
    t = drawing.ax.texts[-1]
    assert t.get_text() == "hello"
    assert tuple(t.get_position()) == pytest.approx((1.0, 2.0))
    assert t.get_fontsize() == pytest.approx(20)
    assert to_rgba(t.get_color()) == to_rgba("purple")


# --------------------------------------------------------------------------- #
# preset system
# --------------------------------------------------------------------------- #


def test_preset_applied_and_overridden_by_kwarg():
    d = Drawing(presets={"node": {"facecolor": "red", "linewidth": 2}})

    d.circle((0, 0), preset="node")
    c1 = d.ax.patches[-1]
    assert to_rgba(c1.get_facecolor()) == to_rgba("red")
    assert c1.get_linewidth() == pytest.approx(2)

    # explicit kwarg must win over the preset
    d.circle((0, 0), preset="node", linewidth=7)
    assert d.ax.patches[-1].get_linewidth() == pytest.approx(7)


def test_unknown_preset_warns(drawing):
    with pytest.warns(UserWarning, match="no preset 'ghost'"):
        drawing.circle((0, 0), preset="ghost")


# --------------------------------------------------------------------------- #
# automatic limit tracking
# --------------------------------------------------------------------------- #


def test_adjust_lims_brackets_drawn_point():
    d = Drawing()
    assert d._xmin is None  # nothing drawn yet
    d.circle((1.0, 2.0), radius=0.25)
    assert d._xmin is not None
    assert d._xmin <= 1.0 <= d._xmax
    assert d._ymin <= 2.0 <= d._ymax
