# src/pyeconomics/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""pyeconomics: open economics and finance models.

This is the 1.0 package skeleton. The version is read from the installed
distribution's metadata, so ``pyproject.toml`` is its only source.

Examples
--------
>>> import pyeconomics
>>> isinstance(pyeconomics.__version__, str)
True
>>> pyeconomics.__version__
'1.0.0...'

"""

from importlib.metadata import version

__version__: str = version("pyeconomics")

__all__ = ["__version__"]
