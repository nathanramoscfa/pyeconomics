# src/pyeconomics/core/rates.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Percent and basis-point conversions at the boundary (ADR-0008 decision 1).

Inside pyeconomics, every rate, return, yield, spread, volatility and
probability is a decimal: ``0.05`` is 5%. Percent and basis points exist only
where people read numbers and where data arrives. Sources such as FRED publish
percent, so the data layer converts them with :func:`percent_to_decimal`.
These functions are the only converters; nothing else multiplies or divides
by 100 or 10,000 to change a rate's scale.

Examples
--------
>>> from pyeconomics.core import format_percent, percent_to_decimal
>>> percent_to_decimal(5.25)
0.0525
>>> format_percent(0.0525)
'5.25%'

"""

from __future__ import annotations

import math
from typing import Final

from pyeconomics.core.errors import InputError

__all__ = [
    "BASIS_POINTS_PER_UNIT",
    "PERCENT_PER_UNIT",
    "basis_points_to_decimal",
    "decimal_to_basis_points",
    "decimal_to_percent",
    "format_basis_points",
    "format_percent",
    "percent_to_decimal",
]

#: Percent in one unit: 1.0 is 100%.
PERCENT_PER_UNIT: Final = 100.0
#: Basis points in one unit: 1.0 is 10,000 bp.
BASIS_POINTS_PER_UNIT: Final = 10_000.0
_MAX_DECIMALS: Final = 10


def _finite(value: float, what: str) -> float:
    if not math.isfinite(value):
        msg = f"{what} must be a finite number, not {value!r}"
        raise InputError(msg)
    return value


def percent_to_decimal(value: float) -> float:
    """Convert a percentage to a decimal.

    Parameters
    ----------
    value
        A percentage, such as ``5.25`` for 5.25%.

    Returns
    -------
    float
        The decimal, such as ``0.0525``.

    Raises
    ------
    InputError
        If ``value`` is NaN or infinite.

    Examples
    --------
    >>> percent_to_decimal(-0.5)
    -0.005

    """
    return _finite(value, "a percentage") / PERCENT_PER_UNIT


def decimal_to_percent(value: float) -> float:
    """Convert a decimal to a percentage.

    The product is a binary float, so it can differ from the exact
    percentage in the last digit (``0.07`` gives ``7.000000000000001``);
    format it for display with :func:`format_percent`.

    Examples
    --------
    >>> decimal_to_percent(0.0525)
    5.25

    """
    return _finite(value, "a decimal") * PERCENT_PER_UNIT


def basis_points_to_decimal(value: float) -> float:
    """Convert basis points to a decimal: 125 bp is ``0.0125``.

    Examples
    --------
    >>> basis_points_to_decimal(125)
    0.0125

    """
    return _finite(value, "a number of basis points") / BASIS_POINTS_PER_UNIT


def decimal_to_basis_points(value: float) -> float:
    """Convert a decimal to basis points: ``0.0125`` is 125 bp.

    Examples
    --------
    >>> decimal_to_basis_points(0.0125)
    125.0

    """
    return _finite(value, "a decimal") * BASIS_POINTS_PER_UNIT


def _format(value: float, scale: float, decimals: int) -> str:
    _finite(value, "a decimal")
    if not 0 <= decimals <= _MAX_DECIMALS:
        msg = f"decimals must be between 0 and {_MAX_DECIMALS}, not {decimals}"
        raise InputError(msg)
    # Adding 0.0 turns a negative zero into zero, so -0.00001 shows as 0.00%.
    shown = round(value * scale, decimals) + 0.0
    return f"{shown:.{decimals}f}"


def format_percent(value: float, *, decimals: int = 2) -> str:
    """Format a decimal as a percentage for display.

    Parameters
    ----------
    value
        A decimal, such as ``0.0525``.
    decimals
        Digits after the decimal point, from 0 to 10.

    Examples
    --------
    >>> format_percent(0.0525)
    '5.25%'
    >>> format_percent(-0.00001)
    '0.00%'
    >>> format_percent(0.123456, decimals=3)
    '12.346%'

    """
    return _format(value, PERCENT_PER_UNIT, decimals) + "%"


def format_basis_points(value: float, *, decimals: int = 0) -> str:
    """Format a decimal as basis points for display.

    Examples
    --------
    >>> format_basis_points(0.0125)
    '125 bp'
    >>> format_basis_points(-0.00015, decimals=1)
    '-1.5 bp'

    """
    return _format(value, BASIS_POINTS_PER_UNIT, decimals) + " bp"
