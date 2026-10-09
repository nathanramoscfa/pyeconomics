# src/pyeconomics/core/compounding.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
r"""Compounding frequencies and rate conversions (ADR-0008 decision 4).

A rate is always quoted with its compounding: simple, periodic at a
:class:`Frequency`, or continuous. The accumulation factor of a decimal rate
:math:`r` over :math:`t` years is

=================  =======================================
Compounding        Accumulation factor
=================  =======================================
simple             :math:`1 + r t`
periodic, m/year   :math:`(1 + r / m)^{m t}`
continuous         :math:`e^{r t}`
=================  =======================================

and its discount factor is the reciprocal. :func:`convert_rate` turns a rate
into the rate with the same accumulation factor under another compounding.
The functions take scalars; a model applies them across arrays.

Examples
--------
>>> from pyeconomics.core import Compounding, Frequency, convert_rate
>>> round(convert_rate(0.06, Compounding.PERIODIC, Compounding.PERIODIC,
...                    from_frequency=Frequency.MONTHLY,
...                    to_frequency=Frequency.ANNUAL), 10)
0.0616778119

"""

from __future__ import annotations

import math
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from pyeconomics.core.errors import DomainError, InputError

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "Compounding",
    "Frequency",
    "accumulation_factor",
    "convert_rate",
    "discount_factor",
    "effective_annual_rate",
    "implied_rate",
]


class Frequency(StrEnum):
    """How many times a year a rate compounds or a payment falls.

    ``DAILY`` is calendar-daily (365 a year). Annualizing a return series is a
    different question: it takes an explicit ``periods_per_year``, such as
    252 trading days, never one guessed from the data.

    Examples
    --------
    >>> Frequency.SEMIANNUAL.periods_per_year
    2
    >>> Frequency.MONTHLY.pandas_alias
    'ME'

    """

    ANNUAL = "annual"
    SEMIANNUAL = "semiannual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"

    @property
    def periods_per_year(self) -> int:
        """The number of periods in one year."""
        return _PERIODS_PER_YEAR[self]

    @property
    def pandas_alias(self) -> str:
        """The pandas 3 offset alias for period-end data at this frequency."""
        return _PANDAS_ALIAS[self]


_PERIODS_PER_YEAR: Final[Mapping[Frequency, int]] = MappingProxyType(
    {
        Frequency.ANNUAL: 1,
        Frequency.SEMIANNUAL: 2,
        Frequency.QUARTERLY: 4,
        Frequency.MONTHLY: 12,
        Frequency.WEEKLY: 52,
        Frequency.DAILY: 365,
    }
)

# pandas 3 removed the M, Q and Y aliases for period ends (ADR-0008 decision 9).
_PANDAS_ALIAS: Final[Mapping[Frequency, str]] = MappingProxyType(
    {
        Frequency.ANNUAL: "YE",
        Frequency.SEMIANNUAL: "6ME",
        Frequency.QUARTERLY: "QE",
        Frequency.MONTHLY: "ME",
        Frequency.WEEKLY: "W",
        Frequency.DAILY: "D",
    }
)


class Compounding(StrEnum):
    """How interest on a rate compounds."""

    SIMPLE = "simple"
    PERIODIC = "periodic"
    CONTINUOUS = "continuous"


def _check(value: float, what: str) -> None:
    if not math.isfinite(value):
        msg = f"{what} must be a finite number, not {value!r}"
        raise InputError(msg)


def _periods(compounding: Compounding, frequency: Frequency | None) -> int:
    """Return m for periodic compounding; reject a frequency it cannot use."""
    if compounding is Compounding.PERIODIC:
        if frequency is None:
            msg = "periodic compounding needs a frequency"
            raise InputError(msg)
        return frequency.periods_per_year
    if frequency is not None:
        msg = f"{compounding.value} compounding takes no frequency"
        raise InputError(msg)
    return 0


def accumulation_factor(
    rate: float,
    years: float,
    compounding: Compounding,
    frequency: Frequency | None = None,
) -> float:
    """Return what one unit grows to at ``rate`` over ``years``.

    Parameters
    ----------
    rate
        The decimal rate per year.
    years
        The horizon in years, zero or more.
    compounding
        How the rate compounds.
    frequency
        The compounding frequency; required for periodic compounding, and
        refused otherwise.

    Raises
    ------
    InputError
        If an argument is not finite, ``years`` is negative, or the
        frequency does not fit the compounding.
    DomainError
        If the factor is not positive: ``1 + r t <= 0`` (simple) or
        ``1 + r / m <= 0`` (periodic).

    Examples
    --------
    >>> accumulation_factor(0.05, 2, Compounding.SIMPLE)
    1.1
    >>> accumulation_factor(0.05, 2, Compounding.PERIODIC, Frequency.ANNUAL)
    1.1025

    """
    _check(rate, "the rate")
    _check(years, "the time in years")
    if years < 0:
        msg = f"the time in years must not be negative, not {years!r}"
        raise InputError(msg)
    m = _periods(compounding, frequency)
    if compounding is Compounding.SIMPLE:
        factor = 1.0 + rate * years
    elif compounding is Compounding.PERIODIC:
        base = 1.0 + rate / m
        if base <= 0:
            msg = f"a rate of {rate!r} compounded {m} times a year is below -100%"
            raise DomainError(msg)
        factor = math.pow(base, m * years)
    else:
        factor = math.exp(rate * years)
    if not factor > 0:
        msg = f"the accumulation factor {factor!r} is not positive"
        raise DomainError(msg)
    return factor


def discount_factor(
    rate: float,
    years: float,
    compounding: Compounding,
    frequency: Frequency | None = None,
) -> float:
    """Return the present value of one unit paid in ``years``.

    It is the reciprocal of :func:`accumulation_factor`, with the same
    arguments and errors.

    Examples
    --------
    >>> round(discount_factor(0.05, 10, Compounding.CONTINUOUS), 12)
    0.606530659713

    """
    return 1.0 / accumulation_factor(rate, years, compounding, frequency)


def implied_rate(
    factor: float,
    years: float,
    compounding: Compounding,
    frequency: Frequency | None = None,
) -> float:
    """Return the rate whose accumulation factor over ``years`` is ``factor``.

    The inverse of :func:`accumulation_factor`. Pass ``1 / df`` to recover the
    rate behind a discount factor ``df``.

    Raises
    ------
    InputError
        If ``factor`` is not positive and finite, or ``years`` is not
        positive.

    Examples
    --------
    >>> round(implied_rate(1.1025, 2, Compounding.PERIODIC, Frequency.ANNUAL), 12)
    0.05

    """
    _check(factor, "the accumulation factor")
    _check(years, "the time in years")
    if factor <= 0:
        msg = f"the accumulation factor must be positive, not {factor!r}"
        raise InputError(msg)
    if years <= 0:
        msg = f"the time in years must be positive, not {years!r}"
        raise InputError(msg)
    m = _periods(compounding, frequency)
    if compounding is Compounding.SIMPLE:
        return (factor - 1.0) / years
    if compounding is Compounding.PERIODIC:
        return m * (math.pow(factor, 1.0 / (m * years)) - 1.0)
    return math.log(factor) / years


def effective_annual_rate(
    rate: float, compounding: Compounding, frequency: Frequency | None = None
) -> float:
    """Return the annually compounded rate equivalent over one year.

    Examples
    --------
    >>> round(effective_annual_rate(0.12, Compounding.PERIODIC,
    ...                             Frequency.MONTHLY), 12)
    0.126825030132

    """
    return accumulation_factor(rate, 1.0, compounding, frequency) - 1.0


def convert_rate(  # noqa: PLR0913 - two compoundings, two frequencies, a horizon
    rate: float,
    from_compounding: Compounding,
    to_compounding: Compounding,
    *,
    from_frequency: Frequency | None = None,
    to_frequency: Frequency | None = None,
    years: float = 1.0,
) -> float:
    """Return the equivalent rate under another compounding.

    Two rates are equivalent when they give the same accumulation factor over
    ``years``. Between periodic and continuous compounding the horizon does
    not matter; with simple interest on either side it does, so pass the
    horizon the simple rate is quoted for.

    Examples
    --------
    >>> round(convert_rate(0.05, Compounding.CONTINUOUS, Compounding.PERIODIC,
    ...                    to_frequency=Frequency.SEMIANNUAL), 12)
    0.050630241049

    """
    factor = accumulation_factor(rate, years, from_compounding, from_frequency)
    return implied_rate(factor, years, to_compounding, to_frequency)
