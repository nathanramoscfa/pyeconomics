# src/pyeconomics/core/_optional.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Lazy imports of the libraries a feature needs but the package does not require.

Polars and pyarrow are never dependencies, not even through an extra (ADR-0008
decision 8), and Plotly belongs to the ``plot`` extra. A conversion that needs
one imports it here, when it is called, and raises
:class:`~pyeconomics.core.errors.MissingOptionalDependencyError` naming what to
install when it is absent.

Examples
--------
>>> import sys
>>> from pyeconomics.core.errors import MissingOptionalDependencyError
>>> sys.modules["not_a_real_package"] = None  # type: ignore[assignment]
>>> try:
...     import_optional("not_a_real_package")
... except MissingOptionalDependencyError as error:
...     print(error)
this feature needs not_a_real_package; install it with: pip install not_a_real_package
>>> del sys.modules["not_a_real_package"]

"""

from __future__ import annotations

import importlib
from typing import Any

from pyeconomics.core.errors import MissingOptionalDependencyError

__all__ = ["import_optional"]


def import_optional(module: str, *, extra: str | None = None) -> Any:  # noqa: ANN401 - a module
    """Import ``module``, or raise naming the package and, if any, the extra.

    Parameters
    ----------
    module
        The dotted module name, such as ``"pyarrow.parquet"``.
    extra
        The pyeconomics extra that installs the package, when it has one.

    Raises
    ------
    MissingOptionalDependencyError
        If the module's top-level package is not installed.
    """
    try:
        return importlib.import_module(module)
    except ImportError as error:
        package = module.partition(".")[0]
        raise MissingOptionalDependencyError(package, extra=extra) from error
