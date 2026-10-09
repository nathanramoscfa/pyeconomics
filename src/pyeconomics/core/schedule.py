# src/pyeconomics/core/schedule.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Backward coupon schedules, with accrual dates separate from payments.

The maturity is the anchor for every shift, preventing clamping drift.
Only the first accrual period can be irregular. The calendar adjusts payment
dates after generation; it never changes the unadjusted accrual boundaries.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Final, Literal

from pyeconomics.core.calendars import BusinessDayConvention, CalendarId, adjust
from pyeconomics.core.compounding import Frequency
from pyeconomics.core.dates import _shift_months, validate_date
from pyeconomics.core.errors import InputError
from pyeconomics.core.units import MAX_ARRAY_LENGTH

__all__ = ["Schedule", "generate"]

_MIN_FULL_PERIOD_BOUNDARIES: Final = 2


@dataclass(frozen=True, slots=True)
class Schedule:
    """Immutable accrual boundaries and one payment date per accrual period."""

    accrual_dates: tuple[dt.date, ...]
    payment_dates: tuple[dt.date, ...]


def _previous(
    maturity: dt.date, frequency: Frequency, periods: int, *, end_of_month: bool
) -> dt.date:
    if frequency in (Frequency.WEEKLY, Frequency.DAILY):
        days = 7 if frequency is Frequency.WEEKLY else 1
        return maturity - dt.timedelta(days=days * periods)
    return _shift_months(
        maturity,
        -periods * (12 // frequency.periods_per_year),
        end_of_month=end_of_month,
    )


def _check_frequency(frequency: object) -> None:
    if not isinstance(frequency, Frequency):
        msg = "frequency must be a Frequency member"
        raise InputError(msg)


def generate(  # noqa: PLR0913 - the public schedule contract's independent options
    effective: dt.date,
    maturity: dt.date,
    frequency: Frequency,
    *,
    stub: Literal["short_front", "long_front"] = "short_front",
    end_of_month: bool,
    calendar: CalendarId | None = None,
    convention: BusinessDayConvention = BusinessDayConvention.UNADJUSTED,
) -> Schedule:
    """Generate backward with an optional short or long front stub.

    ``end_of_month`` preserves calendar month ends when maturity is month-end
    and the frequency is monthly or coarser. Weekly/daily schedules ignore it.
    A long stub removes the first interior date only if a short stub exists.
    InputError rejects reversed/equal dates, unsupported options, schedules
    with no full period, and schedules exceeding MAX_ARRAY_LENGTH boundaries.
    """
    validate_date(effective)
    validate_date(maturity)
    if effective >= maturity:
        msg = "effective must precede maturity"
        raise InputError(msg)
    _check_frequency(frequency)
    if stub not in ("short_front", "long_front"):
        msg = "stub must be short_front or long_front"
        raise InputError(msg)
    # Validate adjustment arguments even if no generated date needs moving.
    adjust(maturity, calendar, convention)
    dates = [maturity]
    periods = 1
    previous = _previous(maturity, frequency, periods, end_of_month=end_of_month)
    if previous < effective:
        msg = "a schedule must contain at least one full period"
        raise InputError(msg)
    while previous > effective:
        dates.append(previous)
        periods += 1
        if periods >= MAX_ARRAY_LENGTH:
            msg = "schedule exceeds MAX_ARRAY_LENGTH accrual boundaries"
            raise InputError(msg)
        previous = _previous(maturity, frequency, periods, end_of_month=end_of_month)
    if previous < effective and stub == "long_front":
        dates.pop()
        if len(dates) < _MIN_FULL_PERIOD_BOUNDARIES:
            msg = "a long-stub schedule must retain at least one full period"
            raise InputError(msg)
    dates.append(effective)
    accrual = tuple(reversed(dates))
    return Schedule(
        accrual, tuple(adjust(day, calendar, convention) for day in accrual[1:])
    )
