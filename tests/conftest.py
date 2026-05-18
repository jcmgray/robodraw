"""Shared fixtures and headless-safe matplotlib config for the test suite."""

import matplotlib

# must happen before any figure is created; Agg has no display dependency
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from robodraw import Drawing  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    """Close every figure after each test so figures don't leak between
    tests (each ``Drawing()`` with no ``ax`` creates a new one)."""
    yield
    plt.close("all")


@pytest.fixture
def drawing():
    """A fresh default :class:`Drawing` (owns its own figure)."""
    return Drawing()
