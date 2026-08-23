"""Unit tests for the pure helper functions in ``robodraw.schematic``.

These have no matplotlib state and are the cheapest things to assert on
exactly, so they get the most thorough coverage.
"""

import math
import warnings

import pytest
from matplotlib.colors import to_rgba

from robodraw.schematic import (
    auto_colors,
    average_color,
    color_oklch,
    darken_color,
    distance,
    gen_points_around,
    get_color,
    get_control_points,
    hash_to_color,
    mean,
    parse_style_preset,
    set_coloring_seed,
    shorten_line,
)

# --------------------------------------------------------------------------- #
# colors
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("l", "expected"),
    [
        (0.0, (0.0, 0.0, 0.0)),
        (0.5, (0.38857286, 0.38857286, 0.38857286)),
        (1.0, (1.0, 1.0, 1.0)),
    ],
)
def test_color_oklch_achromatic(l, expected):
    assert color_oklch(l, 0.0, 0.0) == pytest.approx(expected, abs=1e-7)


def test_color_oklch_hue_wraps_at_one():
    assert color_oklch(0.7, 0.2, 0.0) == color_oklch(0.7, 0.2, 1.0)


def test_color_oklch_known_in_gamut_conversion():
    assert color_oklch(0.7, 0.25, 0.5) == pytest.approx(
        (0.29264201, 0.70096181, 0.63016792),
        abs=1e-7,
    )


def test_color_oklch_out_of_gamut_clip():
    # native oklch(0.69012 0.25077 199.893)
    args = (0.69012, 0.25077 / 0.4, 199.893 / 360.0)
    with pytest.warns(UserWarning, match="outside the sRGB gamut"):
        color = color_oklch(*args)
    assert color == pytest.approx((0.0, 0.76208, 0.84480), abs=1e-5)


def test_color_oklch_out_of_gamut_reduce():
    # native oklch(0.69012 0.25077 199.893)
    args = (0.69012, 0.25077 / 0.4, 199.893 / 360.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        color = color_oklch(*args, gamut="reduce")
    assert color == pytest.approx((0.0, 0.69283, 0.72069), abs=1e-5)


def test_color_oklch_gamut_raise_accepts_in_gamut_color():
    expected = color_oklch(0.7, 0.25, 0.5)
    assert color_oklch(0.7, 0.25, 0.5, gamut="raise") == expected


def test_color_oklch_gamut_raise_rejects_out_of_gamut_color():
    # native oklch(0.69012 0.25077 199.893)
    args = (0.69012, 0.25077 / 0.4, 199.893 / 360.0)
    with pytest.raises(ValueError, match="outside the sRGB gamut"):
        color_oklch(*args, gamut="raise")


@pytest.mark.parametrize(
    ("args", "match"),
    [
        ((-0.1, 0.0, 0.0), "l"),
        ((1.1, 0.0, 0.0), "l"),
        ((0.0, -0.1, 0.0), "c"),
        ((0.0, 1.1, 0.0), "c"),
        ((0.0, 0.0, -0.1), "h"),
        ((0.0, 0.0, 1.1), "h"),
    ],
)
def test_color_oklch_rejects_out_of_range_input(args, match):
    with pytest.raises(ValueError, match=match):
        color_oklch(*args)


def test_color_oklch_rejects_invalid_gamut():
    with pytest.raises(ValueError, match="gamut"):
        color_oklch(0.5, 0.5, 0.5, gamut="compress")


def test_color_oklch_returns_matplotlib_color():
    color = color_oklch(0.6, 0.1, 0.3)
    assert len(color) == 3
    assert all(type(channel) is float for channel in color)
    assert to_rgba(color) == (*color, 1.0)


def test_hash_to_color_deterministic_and_hex():
    a = hash_to_color("hello")
    b = hash_to_color("hello")
    assert a == b
    assert isinstance(a, str) and a.startswith("#")
    # different strings -> (almost certainly) different colors
    assert hash_to_color("hello") != hash_to_color("world")


def test_hash_to_color_responds_to_seed():
    set_coloring_seed(1)
    c1 = hash_to_color("same-string")
    set_coloring_seed(2)
    c2 = hash_to_color("same-string")
    set_coloring_seed(8)  # restore module default
    assert c1 != c2


@pytest.mark.parametrize(
    "name", ["blue", "orange", "green", "red", "yellow", "pink", "bluedark"]
)
def test_get_color_known_names(name):
    rgb = get_color(name)
    assert len(rgb) == 3
    assert all(0.0 <= c <= 1.0 for c in rgb)
    # with alpha -> 4-tuple
    rgba = get_color(name, alpha=0.5)
    assert len(rgba) == 4 and rgba[3] == 0.5


def test_get_color_unknown_raises():
    with pytest.raises(KeyError):
        get_color("chartreuse")


def test_darken_color_scales_rgb_preserves_alpha():
    # red is (1, 0, 0, 1)
    assert darken_color("red", factor=0.5) == pytest.approx(
        (0.5, 0.0, 0.0, 1.0)
    )
    # alpha must be preserved untouched
    out = darken_color((1.0, 1.0, 1.0, 0.25), factor=0.5)
    assert out == pytest.approx((0.5, 0.5, 0.5, 0.25))


def test_average_color_rms():
    out = average_color([(1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0)])
    assert out[0] == pytest.approx((0.5) ** 0.5)
    assert out[1] == pytest.approx(0.0)
    assert out[3] == pytest.approx(1.0)


def test_auto_colors_length_and_alpha():
    cols = auto_colors(5, alpha=0.7)
    assert len(cols) == 5
    assert all(len(c) == 4 and c[3] == 0.7 for c in cols)


def test_auto_colors_default_sequence_limit():
    assert len(auto_colors(7, default_sequence=True)) == 7
    with pytest.raises(ValueError):
        auto_colors(8, default_sequence=True)


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #


def test_distance_and_mean():
    assert distance((0, 0), (3, 4)) == pytest.approx(5.0)
    assert distance((0, 0, 0), (1, 2, 2)) == pytest.approx(3.0)
    assert mean([1, 2, 3, 4]) == pytest.approx(2.5)


def test_shorten_line_2d():
    (xa, ya), (xb, yb) = shorten_line((0.0, 0.0), (10.0, 0.0), 2.0)
    assert (xa, ya) == pytest.approx((2.0, 0.0))
    assert (xb, yb) == pytest.approx((8.0, 0.0))


def test_shorten_line_asymmetric():
    pa, pb = shorten_line((0.0, 0.0), (10.0, 0.0), (1.0, 3.0))
    assert pa == pytest.approx((1.0, 0.0))
    assert pb == pytest.approx((7.0, 0.0))


def test_get_control_points_returns_two_points():
    ca, cb = get_control_points((0, 0), (1, 0), (2, 1))
    assert len(ca) == 2 and len(cb) == 2


def test_gen_points_around_count_and_radius():
    pts = list(gen_points_around((5.0, -3.0), radius=2.0, resolution=8))
    assert len(pts) == 8
    for x, y in pts:
        assert math.hypot(x - 5.0, y + 3.0) == pytest.approx(2.0)


# --------------------------------------------------------------------------- #
# parse_style_preset
# --------------------------------------------------------------------------- #


def test_parse_style_preset_none_and_kwargs():
    presets = {None: {}}
    assert parse_style_preset(presets, None) == {}
    assert parse_style_preset(presets, None, color="red") == {"color": "red"}


def test_parse_style_preset_single_and_override():
    presets = {"p": {"color": "red", "linewidth": 1}}
    assert parse_style_preset(presets, "p") == {"color": "red", "linewidth": 1}
    # explicit kwargs override the preset
    out = parse_style_preset(presets, "p", linewidth=9)
    assert out == {"color": "red", "linewidth": 9}


def test_parse_style_preset_chained_later_wins():
    presets = {"a": {"color": "red"}, "b": {"color": "blue", "lw": 2}}
    out = parse_style_preset(presets, ("a", "b"))
    assert out == {"color": "blue", "lw": 2}


def test_parse_style_preset_warns_on_missing():
    with pytest.warns(UserWarning, match="no preset 'nope'"):
        parse_style_preset({None: {}}, "nope")
