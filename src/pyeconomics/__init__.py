# src/pyeconomics/__init__.py
"""pyeconomics: open economics and finance models.

This is the 1.0 package skeleton. The version is read from the installed
distribution's metadata, so ``pyproject.toml`` is its only source.
"""

from importlib.metadata import version

__version__: str = version("pyeconomics")

__all__ = ["__version__"]
