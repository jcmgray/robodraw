"""Construction variants, coordinate context managers, and file output."""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.transforms import Affine2D

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


@pytest.mark.parametrize(
    "method,radius",
    [
        ("patch_around", 0.0),
        ("patch_around", 0.2),
        ("patch_around_circles", 0.2),
    ],
)
@pytest.mark.parametrize("ndim", [2, 3])
@pytest.mark.parametrize("projection", ["orthographic", "isometric"])
def test_boundary_patch_transforms_applied_once(
    method, radius, ndim, projection
):
    d = Drawing(projection=projection, xscale=1.5, yscale=0.75, zscale=1.25)
    coos = [coo[:ndim] for coo in [(0, 0, 0), (2, 0, 1), (1, 1, 2)]]
    if method == "patch_around_circles":
        coos = coos[:2]
    translated = [
        tuple(c + offset for c, offset in zip(coo, (5, -2, 1))) for coo in coos
    ]
    project = d._3d_project if ndim == 3 else d._2d_project
    projected = [project(*coo) for coo in translated]
    projected = [(x + 3, y + 4) for x, y in projected]

    def draw_patch(drawing, points):
        style = {"linewidth": 2.5, "edgecolor": "red", "zorder_delta": 0.3}
        if method == "patch_around":
            drawing.patch_around(points, radius=radius, **style)
        else:
            drawing.patch_around_circles(
                points[0], radius, points[1], radius * 1.5, **style
            )

    expected = Drawing()
    draw_patch(expected, projected)
    with d.translate(5, -2, 1), d.translate_screen(3, 4):
        draw_patch(d, coos)

    (patch,) = d.ax.patches
    (reference,) = expected.ax.patches
    np.testing.assert_allclose(
        patch.get_path().vertices, reference.get_path().vertices
    )
    np.testing.assert_array_equal(
        patch.get_path().codes, reference.get_path().codes
    )
    zorder = (
        min(d._coo_to_zorder(*coo) for coo in translated) if ndim == 3 else 0
    )
    assert patch.get_zorder() == pytest.approx(zorder + 0.3)
    assert patch.get_linewidth() == reference.get_linewidth()
    assert patch.get_edgecolor() == reference.get_edgecolor()
    assert (d._xmin, d._xmax, d._ymin, d._ymax) == pytest.approx(
        (expected._xmin, expected._xmax, expected._ymin, expected._ymax)
    )


def test_patch_can_use_screen_coordinates():
    coos = [(0, 0), (2, 0), (1, 1)]
    expected = Drawing()
    expected.patch(coos)
    d = Drawing(xscale=1.5, yscale=0.75)
    with d.translate(5, -2), d.translate_screen(3, 4):
        d.patch(coos, project=False)
    np.testing.assert_allclose(
        d.ax.patches[0].get_path().vertices,
        expected.ax.patches[0].get_path().vertices,
    )


@pytest.mark.parametrize("extend", [0.0, 0.5])
@pytest.mark.parametrize("coos", [((0, 0), (2, 0)), ((1, -1), (3, 2))])
@pytest.mark.parametrize(
    "scale,offset,screen_offset",
    [
        ((1, 1), (5, -2), (0, 0)),
        ((1.5, 0.75), (0, 0), (0, 0)),
        ((1, 1), (0, 0), (3, 4)),
        ((-1.5, 0.75), (5, -2), (3, 4)),
    ],
)
def test_cup_transforms_apply_to_arc_and_extensions(
    extend, coos, scale, offset, screen_offset
):
    reference = Drawing()
    reference.cup(*coos, extend=extend)
    d = Drawing(xscale=scale[0], yscale=scale[1])
    with d.translate(*offset), d.translate_screen(*screen_offset):
        d.cup(*coos, extend=extend)

    def project(points):
        points = [
            d._2d_project(x + offset[0], y + offset[1]) for x, y in points
        ]
        return np.array(points) + screen_offset

    (base_arc,) = reference.ax.patches
    base_vertices = base_arc.get_patch_transform().transform(
        base_arc.get_path().vertices
    )
    (arc,) = d.ax.patches
    vertices = d.ax.transData.inverted().transform(
        arc.get_transform().transform(arc.get_path().vertices)
    )
    np.testing.assert_allclose(vertices, project(base_vertices), atol=1e-12)
    assert len(d.ax.lines) == len(reference.ax.lines)
    for line, base_line in zip(d.ax.lines, reference.ax.lines):
        np.testing.assert_allclose(
            line.get_xydata(), project(base_line.get_xydata())
        )
    if extend:
        np.testing.assert_allclose(
            vertices[0], d.ax.lines[1].get_xydata()[-1], atol=1e-12
        )
        np.testing.assert_allclose(
            vertices[-1], d.ax.lines[0].get_xydata()[-1], atol=1e-12
        )

    corners = project(
        [
            (x, y)
            for x in (reference._xmin, reference._xmax)
            for y in (reference._ymin, reference._ymax)
        ]
    )
    assert (d._xmin, d._xmax, d._ymin, d._ymax) == pytest.approx(
        (
            corners[:, 0].min(),
            corners[:, 0].max(),
            corners[:, 1].min(),
            corners[:, 1].max(),
        )
    )


def test_cup_custom_transform_keeps_extensions_connected():
    d = Drawing(xscale=1.5, yscale=0.75)
    transform = Affine2D().rotate_deg(25) + d.ax.transData
    with d.translate(5, -2), d.translate_screen(3, 4):
        d.cup((0, 0), (2, 0), extend=0.5, transform=transform)
    (arc,) = d.ax.patches
    vertices = arc.get_transform().transform(arc.get_path().vertices)
    for vertex, line in zip(vertices[[0, -1]], reversed(d.ax.lines)):
        end = line.get_transform().transform(line.get_xydata()[-1])
        np.testing.assert_allclose(vertex, end)


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
