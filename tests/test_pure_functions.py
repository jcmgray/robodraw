"""Unit tests for the pure helper functions in ``robodraw.schematic``.

These have no matplotlib state and are the cheapest things to assert on
exactly, so they get the most thorough coverage.
"""

import math
import warnings

import pytest
from matplotlib.colors import to_rgba

from robodraw.schematic import (
    _max_srgb_chroma,
    _oklch_to_linear_rgb,
    _srgb_cusp,
    _srgb_encode,
    auto_colors,
    average_color,
    color_okhsl,
    color_okhsv,
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


class TestColorOkhsl:
    @pytest.mark.parametrize("h", [0.0, 0.31, 0.73])
    @pytest.mark.parametrize("l", [0.0, 0.3, 0.5, 0.9, 1.0])
    def test_zero_saturation_is_gray(self, h, l):
        color = color_okhsl(h, 0.0, l)
        assert color == pytest.approx(color_oklch(l, 0.0, h))
        assert color[0] == pytest.approx(color[1]) == pytest.approx(color[2])

    @pytest.mark.parametrize("l", [0.0, 0.5, 1.0])
    def test_hue_wraps_at_one(self, l):
        assert color_okhsl(0.0, 0.8, l) == color_okhsl(1.0, 0.8, l)

    @pytest.mark.parametrize("s", [0.0, 0.5, 1.0])
    @pytest.mark.parametrize("h", [0.08, 0.31, 0.40, 0.73])
    def test_extreme_lightness_is_black_or_white(self, h, s):
        assert color_okhsl(h, s, 0.0) == pytest.approx(
            (0.0, 0.0, 0.0), abs=1e-6
        )
        assert color_okhsl(h, s, 1.0) == pytest.approx(
            (1.0, 1.0, 1.0), abs=1e-6
        )

    @pytest.mark.parametrize("h", [i / 16 for i in range(16)])
    @pytest.mark.parametrize("l", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_full_saturation_is_in_gamut_and_on_boundary(self, h, l):
        color = color_okhsl(h, 1.0, l)
        assert all(0.0 <= channel <= 1.0 for channel in color)
        # at least one linear channel must be at a gamut limit
        assert min(
            min(abs(channel), abs(1.0 - channel))
            for channel in _oklch_to_linear_rgb(l, _max_srgb_chroma(l, h), h)
        ) == pytest.approx(0.0, abs=1e-8)

    @pytest.mark.parametrize("h", [0.08, 0.31, 0.73])
    @pytest.mark.parametrize("l", [0.2, 0.5, 0.8])
    def test_saturation_scales_chroma(self, h, l):
        c_max = _max_srgb_chroma(l, h)
        for s in (0.25, 0.5, 1.0):
            assert color_okhsl(h, s, l) == pytest.approx(
                color_oklch(l, s * c_max / 0.4, h, gamut="raise")
            )

    def test_never_warns_or_clips(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            for h_step in range(11):
                for s_step in range(11):
                    for l_step in range(11):
                        color_okhsl(h_step / 10, s_step / 10, l_step / 10)

    @pytest.mark.parametrize(
        ("args", "match"),
        [
            ((-0.1, 0.0, 0.0), "h"),
            ((1.1, 0.0, 0.0), "h"),
            ((0.0, -0.1, 0.0), "s"),
            ((0.0, 1.1, 0.0), "s"),
            ((0.0, 0.0, -0.1), "l"),
            ((0.0, 0.0, 1.1), "l"),
        ],
    )
    def test_rejects_out_of_range_input(self, args, match):
        with pytest.raises(ValueError, match=match):
            color_okhsl(*args)


class TestColorOkhsv:
    @pytest.mark.parametrize("h", [i / 8 for i in range(8)])
    def test_cusp_matches_brute_force_scan(self, h):
        lightness_min, lightness_max = 0.0, 1.0
        for _ in range(60):
            probe_offset = (lightness_max - lightness_min) / 3
            lower_probe = lightness_min + probe_offset
            upper_probe = lightness_max - probe_offset
            if _max_srgb_chroma(lower_probe, h) < _max_srgb_chroma(
                upper_probe, h
            ):
                lightness_min = lower_probe
            else:
                lightness_max = upper_probe
        lightness = (lightness_min + lightness_max) / 2
        assert _srgb_cusp(h) == pytest.approx(
            (lightness, _max_srgb_chroma(lightness, h)), abs=1e-6
        )

    @pytest.mark.parametrize("h", [0.08, 0.31, 0.73])
    @pytest.mark.parametrize("s", [0.0, 0.5, 1.0])
    def test_zero_value_is_black(self, h, s):
        assert color_okhsv(h, s, 0.0) == pytest.approx((0.0, 0.0, 0.0))

    @pytest.mark.parametrize("h", [0.08, 0.31, 0.73])
    @pytest.mark.parametrize("v", [0.0, 0.4, 1.0])
    def test_zero_saturation_is_gray(self, h, v):
        assert color_okhsv(h, 0.0, v) == pytest.approx(color_oklch(v, 0.0, h))

    @pytest.mark.parametrize("h", [i / 8 for i in range(8)])
    def test_full_saturation_and_value_is_the_cusp(self, h):
        cusp_lightness, cusp_chroma = _srgb_cusp(h)
        assert color_okhsv(h, 1.0, 1.0) == pytest.approx(
            _srgb_encode(_oklch_to_linear_rgb(cusp_lightness, cusp_chroma, h)),
            abs=1e-6,
        )

    @pytest.mark.parametrize("h", [0.08, 0.31, 0.73])
    def test_full_value_zero_saturation_is_white(self, h):
        assert color_okhsv(h, 0.0, 1.0) == pytest.approx((1.0, 1.0, 1.0))

    @pytest.mark.parametrize("h", [i / 16 for i in range(16)])
    @pytest.mark.parametrize("s", [0.25, 0.5, 0.75, 1.0])
    @pytest.mark.parametrize("v", [0.25, 0.5, 0.75, 1.0])
    def test_always_in_gamut(self, h, s, v):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            color = color_okhsv(h, s, v)
        assert all(0.0 <= channel <= 1.0 for channel in color)

    @pytest.mark.parametrize("h", [0.08, 0.31, 0.73])
    @pytest.mark.parametrize("v", [0.4, 0.7, 1.0])
    def test_full_saturation_edge_is_exact(self, h, v):
        # the black-to-cusp boundary is linear and needs no clipping
        cusp_lightness, cusp_chroma = _srgb_cusp(h)
        assert color_okhsv(h, 1.0, v) == pytest.approx(
            _srgb_encode(
                _oklch_to_linear_rgb(
                    v * cusp_lightness,
                    v * cusp_chroma,
                    h,
                )
            ),
            abs=1e-6,
        )

    def test_hue_wraps_at_one(self):
        assert color_okhsv(0.0, 0.8, 0.8) == color_okhsv(1.0, 0.8, 0.8)

    @pytest.mark.parametrize(
        ("args", "match"),
        [
            ((-0.1, 0.0, 0.0), "h"),
            ((1.1, 0.0, 0.0), "h"),
            ((0.0, -0.1, 0.0), "s"),
            ((0.0, 1.1, 0.0), "s"),
            ((0.0, 0.0, -0.1), "v"),
            ((0.0, 0.0, 1.1), "v"),
        ],
    )
    def test_rejects_out_of_range_input(self, args, match):
        with pytest.raises(ValueError, match=match):
            color_okhsv(*args)


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
