"""Construction variants, coordinate context managers, and file output."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from robodraw import Drawing


@pytest.mark.parametrize(
    "projection",
    [
        ("orthographic", 20, 40),
        (20, 40),
        "orthographic",
        "axonometric",
        "isometric",
        ("axonometric", 30, 150),
    ],
)
def test_construct_with_projection_variants(projection):
    d = Drawing(projection=projection)
    # projection is usable
    assert len(d._3d_project(1, 2, 3)) == 2


def test_construct_with_scales_and_presets():
    d = Drawing(xscale=2, yscale=3, presets={"p": {"color": "red"}})
    assert d._2d_project(1, 1) == pytest.approx((2.0, 3.0))
    assert d.presets["p"] == {"color": "red"}


def test_external_ax_disables_lim_adjustment():
    fig, ax = plt.subplots()
    d = Drawing(ax=ax)
    assert d.fig_owner is False
    assert d.adjust_lims is False
    assert d.ax is ax

    xlim_before = ax.get_xlim()
    d.circle((100, 100), radius=1)
    # we don't own the figure, so limits must be left untouched
    assert ax.get_xlim() == xlim_before
    assert d._xmin is None


def test_external_ax_adjust_lims_can_be_forced():
    fig, ax = plt.subplots()
    d = Drawing(ax=ax, adjust_lims=True)
    assert d.adjust_lims is True
    d.circle((5, 5), radius=0.5)
    assert d._xmin is not None


def test_translate_offsets_then_restores(drawing):
    with drawing.translate(10, 5):
        assert drawing._offset == (10, 5, 0)
        drawing.circle((0, 0))
    # restored after the block
    assert drawing._offset == (0, 0, 0)
    assert tuple(drawing.ax.patches[-1].center) == pytest.approx((10.0, 5.0))


def test_translate_permanently_offsets_and_accumulates(drawing):
    drawing.translate(10, 5, 2)
    drawing.translate(-3, 1, 4)
    assert drawing._offset == (7, 6, 6)

    drawing.circle((0, 0))
    assert tuple(drawing.ax.patches[-1].center) == pytest.approx((7.0, 6.0))


def test_translate_context_restores_permanent_offset(drawing):
    drawing.translate(10, 5, 2)
    with drawing.translate(1, 2, 3):
        assert drawing._offset == (11, 7, 5)
    assert drawing._offset == (10, 5, 2)


def test_translate_nested(drawing):
    with drawing.translate(1, 1):
        with drawing.translate(2, 3):
            assert drawing._offset == (3, 4, 0)
        assert drawing._offset == (1, 1, 0)
    assert drawing._offset == (0, 0, 0)


def test_translate_screen_offsets_then_restores(drawing):
    with drawing.translate_screen(3, 4):
        assert drawing._screen_offset == (3, 4)
        drawing.circle((0, 0))
    assert drawing._screen_offset == (0, 0)
    assert tuple(drawing.ax.patches[-1].center) == pytest.approx((3.0, 4.0))


@pytest.mark.parametrize("element", ["o", ".", "star", "cross"])
@pytest.mark.parametrize("coo", [(1, 2), (1, 2, 3)])
@pytest.mark.parametrize("projection", ["orthographic", "isometric"])
def test_marker_translation_and_scaling_applied_once(element, coo, projection):
    d = Drawing(projection=projection, xscale=1.5, yscale=0.75, zscale=1.25)
    translated = tuple(c + offset for c, offset in zip(coo, (5, -2, 1)))
    if len(coo) == 3:
        center = d._3d_project(*translated)
        zorder = d._coo_to_zorder(*translated) + 0.01
    else:
        center = d._2d_project(*translated)
        zorder = 0.01
    center = (center[0] + 3, center[1] + 4)
    radius = 0.2

    with d.translate(5, -2, 1), d.translate_screen(3, 4):
        if element in ("o", "."):
            d.marker(coo, marker=element, radius=radius)
        else:
            getattr(d, element)(coo, radius=radius)

    if element in ("o", "."):
        (circle,) = d.ax.patches
        assert circle.center == pytest.approx(center)
        assert circle.radius == pytest.approx(radius)
        assert circle.get_zorder() == pytest.approx(zorder)
    else:
        assert len(d.ax.lines) == (9 if element == "star" else 4)
        for line in d.ax.lines:
            start, end = line.get_xydata()
            assert start == pytest.approx(center)
            assert np.linalg.norm(end - start) == pytest.approx(radius)
            assert line.get_zorder() == pytest.approx(zorder)


@pytest.mark.parametrize("ext", ["png", "svg"])
def test_savefig_writes_nonempty_file(tmp_path, drawing, ext):
    drawing.circle((0, 0))
    out = tmp_path / f"out.{ext}"
    drawing.savefig(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_translate_line_arrowhead_not_doubly_translated(drawing):
    with drawing.translate(5, 0):
        drawing.line((-0.5, 0.7), (-0.5, -0.5), arrowhead={"center": 1.0})
    arrow, line = drawing.ax.lines
    assert line.get_xydata()[-1] == pytest.approx(
        drawing._2d_project(4.5, -0.5)
    )
    # the arrowhead tip is the middle vertex, here at the line end
    assert arrow.get_xydata()[1] == pytest.approx(
        drawing._2d_project(4.5, -0.5)
    )


def test_translate_line_offset_delegations_not_doubly_translated(drawing):
    with drawing.translate(5, 0):
        drawing.line_offset((0, 0), (2, 0), 0.0, arrowhead=True, text="a")
    (curve,) = drawing.ax.patches
    verts = curve.get_path().vertices
    assert verts[0] == pytest.approx(drawing._2d_project(5, 0))
    assert verts[-1] == pytest.approx(drawing._2d_project(7, 0))
    # arrowhead tip and text both sit halfway along
    (arrow,) = drawing.ax.lines
    assert arrow.get_xydata()[1] == pytest.approx(drawing._2d_project(6, 0))
    (text,) = drawing.ax.texts
    assert text.get_position() == pytest.approx(drawing._2d_project(6, 0))
