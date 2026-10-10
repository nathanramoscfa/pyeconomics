# src/pyeconomics/models/foundations/_common.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""What the foundations models share: input bounds and the output-bound check.

A model's output bounds are sized to its input bounds where that is possible.
Where compounding makes it impossible (a sum growing for a thousand periods), a
value outside an output's bounds has no representable answer, so
:func:`bounded` raises :class:`~pyeconomics.core.DomainError` naming the output,
and the model lists the case in its limitations (ADR-0008 decision 10).
"""

from __future__ import annotations

import math
from typing import Final

from pyeconomics.core import DomainError

__all__ = [
    "LOG_MAX",
    "MONEY_IN",
    "MONEY_OUT",
    "PERIODS_MAX",
    "RATE_MAX",
    "RATE_MIN",
    "bounded",
    "scaled",
]

#: The largest argument ``math.exp`` takes without overflowing: the log of the
#: largest double.
LOG_MAX: Final = math.log(1.7976931348623157e308)
#: The largest amount of money an input may hold.
MONEY_IN: Final = 1e12
#: The largest amount of money an output may hold: ADR-0008's default.
MONEY_OUT: Final = 1e15
#: The default bounds of a rate (ADR-0008 decision 3), used per period too.
RATE_MIN: Final = -0.99
RATE_MAX: Final = 10.0
#: The most periods a time-value calculation spans: 100 years of months.
PERIODS_MAX: Final = 1_200


def bounded(value: float, low: float, high: float, what: str) -> float:
    """Return ``value`` if it is finite and within ``[low, high]``.

    Raises
    ------
    DomainError
        Otherwise, naming the output and its bounds.
    """
    if not (math.isfinite(value) and low <= value <= high):
        msg = (
            f"the {what} is {value!r}, outside its bounds [{low:g}, {high:g}]; "
            "the inputs have no answer this model can represent"
        )
        raise DomainError(msg)
    return value


def scaled(amount: float, factor: float) -> float:
    """Return ``amount * factor``, taking a zero amount to zero.

    A factor can be infinite (a sum compounded for too long); a zero amount
    still contributes nothing, where the plain product would be NaN.
    """
    return 0.0 if amount == 0 else amount * factor
