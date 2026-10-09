# src/pyeconomics/core/dates.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Bounded calendar-date arithmetic (ADR-0008 decisions 3 and 5).

Month shifts clamp a missing day to the destination month's last day. With
``end_of_month=True``, a month-end input stays at month-end.

>>> import datetime as dt
>>> add_months(dt.date(2024, 2, 29), 1, end_of_month=True)
datetime.date(2024, 3, 31)
"""

from __future__ import annotations

import calendar
import datetime as dt

from pyeconomics.core.errors import InputError
from pyeconomics.core.units import DEFAULT_DATE_BOUNDS

__all__ = ["actual_days", "add_months", "add_years", "is_end_of_month", "validate_date"]


def validate_date(value: object) -> dt.date:
    """Return a date in 1900-01-01 through 2200-12-31; refuse datetimes.

    Raises
    ------
    InputError
        If the input is not a date or lies outside ADR-0008's bounds.
    """
    if not isinstance(value, dt.date) or isinstance(value, dt.datetime):
        msg = "a calendar date is required, without a time of day"
        raise InputError(msg)
    if not DEFAULT_DATE_BOUNDS.contains(value):
        msg = "date must be between 1900-01-01 and 2200-12-31"
        raise InputError(msg)
    return value


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = "the date offset must be an integer, not a bool or fraction"
        raise InputError(msg)
    return value


def is_end_of_month(value: dt.date) -> bool:
    """Return whether the bounded date is the last calendar day of its month."""
    validate_date(value)
    return value.day == calendar.monthrange(value.year, value.month)[1]


def _shift_months(value: dt.date, months: int, *, end_of_month: bool) -> dt.date:
    """Shift an internal quasi-coupon date, which may lie just outside bounds."""
    year, month = divmod(value.year * 12 + value.month - 1 + months, 12)
    last = calendar.monthrange(year, month + 1)[1]
    eom = value.day == calendar.monthrange(value.year, value.month)[1]
    day = last if end_of_month and eom else min(value.day, last)
    return dt.date(year, month + 1, day)


def add_months(value: dt.date, months: int, *, end_of_month: bool = False) -> dt.date:
    """Shift by whole months, clamping missing days and optionally preserving EOM.

    Input and result must both satisfy :func:`validate_date`. Repeated shifts
    can lose a clamped day: shift from the original anchor for a schedule.
    """
    validate_date(value)
    _integer(months)
    target = value.year * 12 + value.month - 1 + months
    if not 1900 * 12 <= target < 2201 * 12:
        msg = "date result must be between 1900-01-01 and 2200-12-31"
        raise InputError(msg)
    return _shift_months(value, months, end_of_month=end_of_month)


def add_years(value: dt.date, years: int, *, end_of_month: bool = False) -> dt.date:
    """Shift by whole years using the same rule as :func:`add_months`."""
    return add_months(value, 12 * _integer(years), end_of_month=end_of_month)


def actual_days(start: dt.date, end: dt.date) -> int:
    """Return signed actual calendar days, including start and excluding end."""
    return (validate_date(end) - validate_date(start)).days
