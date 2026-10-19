# Changelog

Release notes are maintained on the [GitHub releases page](https://github.com/jcmgray/robodraw/releases).

## v0.1.1 (unreleased)

**Features:**

- Add [`color_oklch`](#color_oklch), [`color_okhsl`](#color_okhsl) and [`color_okhsv`](#color_okhsv) for choosing colors with inputs in `[0, 1]`. They return RGB colors ready to use with matplotlib.
- Allow [`Drawing.translate`](#Drawing.translate) to set a permanent offset when called directly. Using it in a `with` block still gives a temporary offset.
- Use a subtler default grid color and opacity for dark backgrounds.
- Add a broad test suite, contribution and development guides, and a code of conduct.
- Add a tool to turn changelog references into links for github release notes.
- Update CI and release actions, add monthly Dependabot updates for github actions

**Bug Fixes:**

- Fix arrowheads, labels and offset curves being translated or scaled twice when drawn by [`Drawing.line`](#Drawing.line) or [`Drawing.line_offset`](#Drawing.line_offset).
- Fix circular markers, stars and crosses being translated or scaled twice.
- Fix [`Drawing.patch_around`](#Drawing.patch_around) and [`Drawing.patch_around_circles`](#Drawing.patch_around_circles) applying translation and scaling twice.
- Make the straight sections of [`Drawing.cup`](#Drawing.cup) match the arc's color, linewidth, line style, opacity and depth order.
- Fix presets causing invalid matplotlib keyword errors in compound elements, or infinite recursion for arrowheads with `reverse="both"`.
- Make [`Drawing.curve`](#Drawing.curve) shorten its endpoints before projection, matching lines, zigzags and Bezier curves. This changes endpoint positions for shortened curves drawn with projection or scaling.
- Fix `arrowhead=False` raising an error in `line` and `line_offset`.
- Fix README image links and API documentation links.
