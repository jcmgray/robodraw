from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("robodraw")
except _PackageNotFoundError:
    try:
        # fallback for source trees where hatch-vcs has generated _version.py.
        from ._version import version as __version__
    except ImportError:
        __version__ = "0.0.0+unknown"


from .schematic import (
    Drawing,
    darken_color,
    get_color,
    hash_to_color,
)

__all__ = (
    "darken_color",
    "Drawing",
    "hash_to_color",
    "get_color",
)
