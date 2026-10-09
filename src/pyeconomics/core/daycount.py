# src/pyeconomics/core/daycount.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The six day-count definitions chosen in ADR-0008 decision 5.

Sources: 2006 ISDA Definitions section 4.16; ICMA Rule 251.1(iii), also
described in Primary Market Handbook Appendix A5 (March 2022); QuantLib's
``Thirty360::USA`` convention. Links are recorded in ADR-0008 [S5-S7].
All fractions include the start date and exclude the end date. Reversing
dates negates the result, including for the asymmetric US 30/360 rules.

>>> import datetime as dt
>>> year_fraction(dt.date(2024, 1, 1), dt.date(2024, 7, 1), DayCount.ACT_360)
0.5055555555555555
"""

from __future__ import annotations

import calendar
import datetime as dt
from enum import StrEnum
from itertools import pairwise

from pyeconomics.core.compounding import Frequency
from pyeconomics.core.dates import _shift_months, is_end_of_month, validate_date
from pyeconomics.core.errors import InputError

__all__ = ["DayCount", "year_fraction"]

_LAST_DAY = 31
_THIRTY = 30


class DayCount(StrEnum):
    """Closed day-count vocabulary; each member names its defining section."""

    THIRTY_360_US = "thirty_360_us"
    """US 30/360: QuantLib Thirty360::USA, end-of-month rules (ADR-0008 S7)."""
    THIRTY_E_360 = "thirty_e_360"
    """European 30/360: 2006 ISDA Definitions section 4.16."""
    ACT_360 = "act_360"
    """Actual days / 360: 2006 ISDA Definitions section 4.16."""
    ACT_365_FIXED = "act_365_fixed"
    """Actual days / 365: 2006 ISDA Definitions section 4.16."""
    ACT_ACT_ISDA = "act_act_isda"
    """Actual days split by calendar year: ISDA Definitions section 4.16."""
    ACT_ACT_ICMA = "act_act_icma"
    """Actual days in notional coupon periods: ICMA Rule 251.1(iii)."""


def _thirty_days(start: dt.date, end: dt.date, *, usa: bool) -> int:
    first, last = start.day, end.day
    if usa:
        first_feb = start.month == calendar.FEBRUARY and is_end_of_month(start)
        last_feb = end.month == calendar.FEBRUARY and is_end_of_month(end)
        if first_feb and last_feb:
            last = 30
        if first_feb or first == _LAST_DAY:
            first = 30
        if last == _LAST_DAY and first >= _THIRTY:
            last = 30
    else:
        first, last = min(first, 30), min(last, 30)
    return 360 * (end.year - start.year) + 30 * (end.month - start.month) + last - first


def _isda(start: dt.date, end: dt.date) -> float:
    first_den = 366 if calendar.isleap(start.year) else 365
    if start.year == end.year:
        return (end - start).days / first_den
    # Whole intervening years avoid accumulated rounding on long horizons.
    result = float(end.year - start.year - 1)
    result += (dt.date(start.year + 1, 1, 1) - start).days / first_den
    result += (end - dt.date(end.year, 1, 1)).days / (
        366 if calendar.isleap(end.year) else 365
    )
    return result


def _icma(
    start: dt.date,
    end: dt.date,
    reference_start: dt.date,
    reference_end: dt.date,
    frequency: Frequency,
) -> float:
    """Partition irregular periods into regular notional coupon periods.

    The supplied reference period fixes its two anchors. Earlier notional
    dates step backward from reference_start; later ones shift reference_end.
    Each backward step clamps a missing day without assuming an EOM rule.
    This is QuantLib ActualActual(ISMA)'s explicit-reference interpretation.
    """
    months = 12 // frequency.periods_per_year
    earlier = [reference_start]
    while start < earlier[-1]:
        earlier.append(_shift_months(earlier[-1], -months, end_of_month=False))
    dates = [*reversed(earlier), reference_end]
    index = 1
    while dates[-1] < end:
        dates.append(_shift_months(reference_end, index * months, end_of_month=False))
        index += 1
    result = 0.0
    for left, right in pairwise(dates):
        overlap = (min(end, right) - max(start, left)).days
        if overlap > 0:
            result += overlap / (right - left).days / frequency.periods_per_year
    return result


def _reference(
    reference_start: dt.date | None,
    reference_end: dt.date | None,
    frequency: object,
) -> tuple[dt.date, dt.date, Frequency]:
    if reference_start is None or reference_end is None or frequency is None:
        msg = "ACT_ACT_ICMA requires reference_start, reference_end and frequency"
        raise InputError(msg)
    validate_date(reference_start)
    validate_date(reference_end)
    if (
        not isinstance(frequency, Frequency)
        or frequency.periods_per_year > Frequency.MONTHLY.periods_per_year
    ):
        msg = "ICMA requires an annual, semiannual, quarterly or monthly frequency"
        raise InputError(msg)
    months = 12 // frequency.periods_per_year
    # Either anchor can have been clamped (e.g. Aug 31 to Feb 28).
    forward = _shift_months(reference_start, months, end_of_month=False)
    backward = _shift_months(reference_end, -months, end_of_month=False)
    if reference_start >= reference_end or (
        forward != reference_end and backward != reference_start
    ):
        msg = "reference dates must describe one regular coupon period at the frequency"
        raise InputError(msg)
    return reference_start, reference_end, frequency


def _check_convention(convention: object) -> None:
    if not isinstance(convention, DayCount):
        msg = "convention must be a DayCount member"
        raise InputError(msg)


def year_fraction(  # noqa: PLR0913 - ICMA's explicit reference coupon inputs
    start: dt.date,
    end: dt.date,
    convention: DayCount,
    *,
    reference_start: dt.date | None = None,
    reference_end: dt.date | None = None,
    frequency: Frequency | None = None,
) -> float:
    """Return signed years between dates under a declared day count.

    ICMA requires a regular reference coupon period and a monthly or coarser
    frequency. It divides irregular periods at notional coupon dates. Other
    conventions reject all reference arguments. Invalid inputs, including
    dates outside 1900-2200, raise :class:`InputError`, even for equal dates.
    """
    validate_date(start)
    validate_date(end)
    _check_convention(convention)
    reference = None
    if convention is DayCount.ACT_ACT_ICMA:
        reference = _reference(reference_start, reference_end, frequency)
    elif any(
        value is not None for value in (reference_start, reference_end, frequency)
    ):
        msg = "this day-count convention takes no reference arguments or frequency"
        raise InputError(msg)
    sign = 1.0
    if start > end:
        start, end, sign = end, start, -1.0
    if start == end:
        return 0.0
    if reference is not None:
        return sign * _icma(start, end, *reference)
    if convention is DayCount.ACT_ACT_ISDA:
        return sign * _isda(start, end)
    if convention in (DayCount.THIRTY_360_US, DayCount.THIRTY_E_360):
        return (
            sign
            * _thirty_days(start, end, usa=convention is DayCount.THIRTY_360_US)
            / 360
        )
    denominator = 360 if convention is DayCount.ACT_360 else 365
    return sign * (end - start).days / denominator
