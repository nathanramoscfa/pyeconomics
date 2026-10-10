# src/pyeconomics/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""pyeconomics: open economics and finance models.

The version is read from the installed distribution's metadata, so
``pyproject.toml`` is its only source. :mod:`pyeconomics.registry` finds the
registered models; importing the package discovers none of them.

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

from pyeconomics import registry

__all__ = ["__version__", "registry"]
