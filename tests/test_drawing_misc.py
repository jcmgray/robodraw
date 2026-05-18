"""Construction variants, coordinate context managers, and file output."""

import matplotlib.pyplot as plt
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


@pytest.mark.parametrize("ext", ["png", "svg"])
def test_savefig_writes_nonempty_file(tmp_path, drawing, ext):
    drawing.circle((0, 0))
    out = tmp_path / f"out.{ext}"
    drawing.savefig(out)
    assert out.exists()
    assert out.stat().st_size > 0
