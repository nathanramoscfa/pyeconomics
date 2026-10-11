# src/pyeconomics/core/curves.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
r"""Zero curves: interpolation, discount factors, forward and par rates.

A zero (spot) curve is a set of nodes: increasing tenors in years and the zero
rate at each, quoted with one compounding (ADR-0008 decision 4). Between nodes
the rate is interpolated linearly; before the first node and after the last it
is held flat. The discount factor at time :math:`t` is the reciprocal of the
accumulation factor of the interpolated rate :math:`z(t)` over :math:`t`
(:func:`~pyeconomics.core.compounding.discount_factor`).

Two relations every curve-based model uses:

- the forward rate between :math:`t_1` and :math:`t_2` is the rate whose
  accumulation factor over :math:`t_2 - t_1` is
  :math:`A(z_2, t_2) / A(z_1, t_1)`;
- the par rate of a schedule with accrual fractions :math:`\alpha_i` and
  discount factors :math:`d_i` is :math:`(1 - d_n) / \sum_i \alpha_i d_i`, the
  coupon that prices a bond, or the fixed rate that prices a swap, at par.

The functions take plain sequences and return floats, and do no I/O.

Examples
--------
>>> from pyeconomics.core import Compounding, forward_rate, interpolate_rate
>>> interpolate_rate((1.0, 2.0), (0.03, 0.04), 1.5)
0.035
>>> round(forward_rate(0.03, 1.0, 0.04, 2.0, Compounding.CONTINUOUS), 12)
0.05

"""

from __future__ import annotations

import bisect
import math
from itertools import pairwise
from typing import TYPE_CHECKING

from pyeconomics.core.compounding import (
    Compounding,
    Frequency,
    accumulation_factor,
    discount_factor,
    implied_rate,
)
from pyeconomics.core.errors import InputError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "curve_discount_factors",
    "forward_rate",
    "interpolate_rate",
    "par_rate",
]


def _check_nodes(tenors: Sequence[float], rates: Sequence[float]) -> None:
    if len(tenors) == 0 or len(tenors) != len(rates):
        msg = "a curve needs at least one node and one rate per tenor"
        raise InputError(msg)
    if not all(math.isfinite(t) and t > 0 for t in tenors):
        msg = "curve tenors must be finite and positive"
        raise InputError(msg)
    if any(later <= earlier for earlier, later in pairwise(tenors)):
        msg = "curve tenors must be strictly increasing"
        raise InputError(msg)
    if not all(math.isfinite(r) for r in rates):
        msg = "curve rates must be finite"
        raise InputError(msg)


def interpolate_rate(
    tenors: Sequence[float], rates: Sequence[float], time: float
) -> float:
    """Return the zero rate at ``time``: linear between nodes, flat outside.

    Raises
    ------
    InputError
        If the nodes are empty, of different lengths, not positive and strictly
        increasing, or not finite, or ``time`` is not finite.

    Examples
    --------
    >>> interpolate_rate((1.0, 2.0), (0.03, 0.04), 0.5)
    0.03
    >>> interpolate_rate((1.0, 2.0), (0.03, 0.04), 5.0)
    0.04

    """
    _check_nodes(tenors, rates)
    if not math.isfinite(time):
        msg = f"the time must be finite, not {time!r}"
        raise InputError(msg)
    if time <= tenors[0]:
        return float(rates[0])
    if time >= tenors[-1]:
        return float(rates[-1])
    right = bisect.bisect_right(tenors, time)
    left = right - 1
    weight = (time - tenors[left]) / (tenors[right] - tenors[left])
    return float(rates[left] + weight * (rates[right] - rates[left]))


def curve_discount_factors(
    tenors: Sequence[float],
    rates: Sequence[float],
    times: Sequence[float],
    compounding: Compounding,
    frequency: Frequency | None = None,
) -> list[float]:
    """Return the discount factor at each time, off the interpolated curve.

    Parameters
    ----------
    tenors, rates
        The curve's nodes: tenors in years, strictly increasing, and the zero
        rate at each.
    times
        When each discount factor applies, in years; zero or more.
    compounding, frequency
        How the zero rates compound; periodic compounding needs a frequency.

    Raises
    ------
    InputError
        As for :func:`interpolate_rate`, or a negative time.
    DomainError
        If a rate's accumulation factor is not positive.

    Examples
    --------
    >>> [round(d, 10) for d in curve_discount_factors(
    ...     (1.0,), (0.05,), (1.0, 2.0), Compounding.PERIODIC, Frequency.ANNUAL)]
    [0.9523809524, 0.9070294785]

    """
    return [
        discount_factor(interpolate_rate(tenors, rates, t), t, compounding, frequency)
        for t in times
    ]


def forward_rate(  # noqa: PLR0913 - two (rate, time) points and the compounding
    rate_1: float,
    years_1: float,
    rate_2: float,
    years_2: float,
    compounding: Compounding,
    *,
    frequency: Frequency | None = None,
) -> float:
    """Return the rate from ``years_1`` to ``years_2`` implied by two zero rates.

    Both zero rates, and the forward rate returned, are quoted with the same
    compounding.

    Raises
    ------
    InputError
        If ``years_2`` is not after ``years_1``, or ``years_1`` is negative.
    DomainError
        If an accumulation factor is not positive.

    Examples
    --------
    >>> round(forward_rate(0.04, 1.0, 0.05, 2.0, Compounding.PERIODIC,
    ...                    frequency=Frequency.ANNUAL), 12)
    0.060096153846

    """
    if not (math.isfinite(years_1) and math.isfinite(years_2)):
        msg = "the times must be finite"
        raise InputError(msg)
    if years_1 < 0 or years_2 <= years_1:
        msg = (
            f"the forward period must run forward from a time of zero or more; "
            f"got {years_1!r} to {years_2!r}"
        )
        raise InputError(msg)
    if compounding is Compounding.CONTINUOUS:
        # Exact in rates: no ratio of factors that could overflow.
        return (rate_2 * years_2 - rate_1 * years_1) / (years_2 - years_1)
    near = accumulation_factor(rate_1, years_1, compounding, frequency)
    far = accumulation_factor(rate_2, years_2, compounding, frequency)
    return implied_rate(far / near, years_2 - years_1, compounding, frequency)


def par_rate(discount_factors: Sequence[float], accruals: Sequence[float]) -> float:
    r"""Return :math:`(1 - d_n) / \sum_i \alpha_i d_i`, the par coupon rate.

    Parameters
    ----------
    discount_factors
        The discount factor at each payment date, the last at maturity.
    accruals
        Each period's accrual fraction in years (``0.5`` for a semiannual
        coupon).

    Raises
    ------
    InputError
        If the sequences are empty, differ in length, hold a non-positive
        accrual or discount factor, or are not finite.

    Examples
    --------
    >>> round(par_rate((0.95, 0.9), (1.0, 1.0)), 12)
    0.054054054054

    """
    if len(discount_factors) == 0 or len(discount_factors) != len(accruals):
        msg = "give one accrual fraction per discount factor, at least one"
        raise InputError(msg)
    if not all(math.isfinite(d) and d > 0 for d in discount_factors):
        msg = "discount factors must be finite and positive"
        raise InputError(msg)
    if not all(math.isfinite(a) and a > 0 for a in accruals):
        msg = "accrual fractions must be finite and positive"
        raise InputError(msg)
    annuity = math.fsum(a * d for a, d in zip(accruals, discount_factors, strict=True))
    return (1.0 - discount_factors[-1]) / annuity
