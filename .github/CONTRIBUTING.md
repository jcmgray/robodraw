# Contributing

Thanks for helping improve `robodraw`.

## Development Setup

This project uses pixi. From the repository root:

```bash
pixi install
pixi run -e test pytest
```

For a focused test, run:

```bash
pixi run -e test pytest tests/test_elements.py::test_element_smoke_adds_artist -q
```

## Checks

Before opening a pull request, run the checks that match the change:

```bash
pixi run lint
pixi run -e test test
pixi run docs
```

Use `pixi run format` for code formatting. Use `pixi run format-all` only when
you intentionally want to format notebooks as well.

## Notes

- Most code lives in `robodraw/schematic.py`.
- Tests should assert on matplotlib artists and helper functions rather than
  image snapshots.
- Documentation API pages are generated from docstrings, so keep public
  docstrings clear and complete.
