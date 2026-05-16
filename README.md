<img src="docs/_static/robodraw-header.png" alt="robodraw logo" width="640">

[![tests](https://github.com/jcmgray/robodraw/actions/workflows/tests.yml/badge.svg)](https://github.com/jcmgray/robodraw/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/jcmgray/robodraw/branch/main/graph/badge.svg?token=Q5evNiuT9S)](https://codecov.io/gh/jcmgray/robodraw)
[![Docs](https://readthedocs.org/projects/robodraw/badge/?version=latest)](https://robodraw.readthedocs.io)
[![PyPI](https://img.shields.io/pypi/v/robodraw?color=teal)](https://pypi.org/project/robodraw/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/robodraw/badges/version.svg)](https://anaconda.org/conda-forge/robodraw)
[![Pixi Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)

`robodraw` is an ergonomic and programmatic drawing library for python. It is a
wrapper around `matplotlib` that provides a more intuitive way to specifically
create *drawings and diagrams*, including in pseudo-3d. It provides the backend
for the drawing functionality in [`quimb`](https://quimb.readthedocs.io) and
[`cotengra`](https://cotengra.readthedocs.io).

Some useful features include:

- no boilerplate to get a simple drawing.
- plot limits automatially expand to fit all drawn elements.
- style presets: reuse style across elements.
- diagram primitives like `zigzag`, `curve` (draw a smooth line through an
  arbitrary set of points exactly), and `patch_around` (draw a smooth shape
  highlighting an arbitrary set of points).
- pseudo-3d drawing, with automatic perspective and occlusion handling.
- squared paper grid to help you with placement.
- output or use existing matplotlib figure and axis.
- basic colors tools
- ... and more!

A quick example:

```python
import robodraw

d = robodraw.Drawing(
    presets={
        "node": {"radius": 0.2, "linewidth": 0.5},
        "edge": {"color": (0, 0.3, 1, .8), "width": 0.04, "shorten": 0.2}
    },
    projection=(25, 25),
)

center = (0, 0, 0)
corners = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]

# nodes
for c in corners:
    color = robodraw.hash_to_color(str(c))
    d.circle(c, preset='node', color=color)

# center
d.circle(center, preset='node', radius=0.15, color="black")
d.text(center, "$\\psi$", color="yellow")

# edges to center
for c in corners:
    d.zigzag(c, center, preset="edge")

d.patch_around(corners, radius=0.5)
d.grid3d()
```

<img src="docs/_static/robodraw-simple-example.png" alt="robodraw simple example" width="480">

The **full documentation** can be found at:
[robodraw.readthedocs.io](https://robodraw.readthedocs.io). Contributions of
any sort are very welcome - please see the
[contributing guide](https://github.com/jcmgray/robodraw/blob/main/.github/CONTRIBUTING.md).
[Issues](https://github.com/jcmgray/robodraw/issues) and
[pull requests](https://github.com/jcmgray/robodraw/pulls) are hosted on
[github](https://github.com/jcmgray/robodraw). For other questions and
suggestions, please use the
[discussions page](https://github.com/jcmgray/robodraw/discussions).