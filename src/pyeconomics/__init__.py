# src/pyeconomics/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""pyeconomics: open economics and finance models.

The version is read from the installed distribution's metadata, so
``pyproject.toml`` is its only source. :mod:`pyeconomics.registry` finds the
registered models; importing the package discovers none of them. :func:`run` and
:func:`run_batch` run a registered model and return a result with its manifest.

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
from pyeconomics.core.runner import run, run_batch

__all__ = ["__version__", "registry", "run", "run_batch"]
