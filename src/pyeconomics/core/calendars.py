# src/pyeconomics/core/calendars.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Business-day arithmetic over stable ids backed by ``holidays``.

Mappings (holidays 0.106): ``weekends_only`` has no holidays;
``us_federal`` is country US (federal public holidays, observed=True);
``us_nyse`` is financial XNYS; ``target2`` is financial XECB;
``uk_england`` is country GB, subdivision ENG. These calendars use their
provider's historical rules, including documented differences from QuantLib;
the exhaustive 2000-2030 comparison in test_calendars lists those dates.
Provider calendars end in 2100; TARGET begins in 1999. Outside a provider's
declared years, InputError replaces the provider's silently empty holiday set.
``weekends_only`` supports the full date range.

Definitions: https://holidays.readthedocs.io/en/latest/ (country and financial
calendars). No current date, mutable public calendar or runtime I/O is used.

>>> import datetime as dt
>>> adjust(dt.date(2026, 7, 4), 'us_federal', BusinessDayConvention.FOLLOWING)
datetime.date(2026, 7, 6)
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from functools import lru_cache
from typing import Final, Literal

import holidays

from pyeconomics.core.dates import _integer, validate_date
from pyeconomics.core.errors import InputError

__all__ = [
    "CALENDAR_IDS",
    "BusinessDayConvention",
    "CalendarId",
    "add_business_days",
    "adjust",
    "is_business_day",
]

type CalendarId = Literal[
    "weekends_only", "us_federal", "us_nyse", "target2", "uk_england"
]

CALENDAR_IDS: Final[tuple[CalendarId, ...]] = (
    "weekends_only",
    "us_federal",
    "us_nyse",
    "target2",
    "uk_england",
)
_WEEKEND_START: Final = 5


class BusinessDayConvention(StrEnum):
    """Payment-date adjustments; modified rules stay in the original month."""

    UNADJUSTED = "unadjusted"
    FOLLOWING = "following"
    MODIFIED_FOLLOWING = "modified_following"
    PRECEDING = "preceding"
    MODIFIED_PRECEDING = "modified_preceding"


def _calendar_id(calendar: CalendarId) -> None:
    if calendar not in CALENDAR_IDS:
        msg = f"unknown calendar id {calendar!r}; choose one of {CALENDAR_IDS}"
        raise InputError(msg)


@lru_cache(maxsize=512)
def _holidays(calendar: CalendarId, year: int) -> frozenset[dt.date]:
    # Adjacent years include a next New Year's Day observed on Dec 31.
    # Explicit years and expand=False prevent provider clock defaults and
    # membership lookups from mutating cached state.
    years = [year - 1, year, year + 1]
    if calendar == "weekends_only":
        return frozenset()
    if calendar == "us_federal":
        days = holidays.country_holidays("US", years=years, observed=True, expand=False)
    elif calendar == "uk_england":
        days = holidays.country_holidays(
            "GB", subdiv="ENG", years=years, observed=True, expand=False
        )
    else:
        days = holidays.financial_holidays(
            "XNYS" if calendar == "us_nyse" else "XECB",
            years=years,
            observed=True,
            expand=False,
        )
    if not days.start_year <= year <= days.end_year:
        msg = (
            f"calendar {calendar!r} supports years {days.start_year}-{days.end_year}, "
            f"not {year}"
        )
        raise InputError(msg)
    return frozenset(days)


def is_business_day(value: dt.date, calendar: CalendarId) -> bool:
    """Return whether a bounded date is neither a weekend nor a holiday."""
    validate_date(value)
    _calendar_id(calendar)
    days = _holidays(calendar, value.year)
    return value.weekday() < _WEEKEND_START and value not in days


def _walk(value: dt.date, calendar: CalendarId, direction: int) -> dt.date:
    while not is_business_day(value, calendar):
        value = validate_date(value + dt.timedelta(days=direction))
    return value


def _check_convention(convention: object) -> None:
    if not isinstance(convention, BusinessDayConvention):
        msg = "convention must be a BusinessDayConvention member"
        raise InputError(msg)


def adjust(
    value: dt.date,
    calendar: CalendarId | None = None,
    convention: BusinessDayConvention = BusinessDayConvention.UNADJUSTED,
) -> dt.date:
    """Adjust a bounded date using the specified holiday calendar.

    UNADJUSTED needs no calendar. Other conventions require an explicit id.
    Unknown conventions/ids and a result outside date bounds raise InputError.
    """
    validate_date(value)
    _check_convention(convention)
    if calendar is not None:
        _calendar_id(calendar)
    if convention is BusinessDayConvention.UNADJUSTED:
        return value
    if calendar is None:
        msg = "a business-day adjustment requires an explicit calendar"
        raise InputError(msg)
    following = convention in (
        BusinessDayConvention.FOLLOWING,
        BusinessDayConvention.MODIFIED_FOLLOWING,
    )
    direction = 1 if following else -1
    modified = convention in (
        BusinessDayConvention.MODIFIED_FOLLOWING,
        BusinessDayConvention.MODIFIED_PRECEDING,
    )
    # A modified rule must reverse before walking outside the allowed range.
    candidate = value
    while not is_business_day(candidate, calendar):
        next_date = candidate + dt.timedelta(days=direction)
        if modified and next_date.month != value.month:
            return _walk(value, calendar, -direction)
        candidate = validate_date(next_date)
    return candidate


def add_business_days(value: dt.date, days: int, calendar: CalendarId) -> dt.date:
    """Advance by signed business days, excluding the start; zero adjusts following.

    The zero rule matches QuantLib Calendar.advance. No date outside the
    declared bounds is returned, and offsets must be integers.
    """
    validate_date(value)
    _calendar_id(calendar)
    _integer(days)
    if days == 0:
        return adjust(value, calendar, BusinessDayConvention.FOLLOWING)
    direction = 1 if days > 0 else -1
    for _ in range(abs(days)):
        value = validate_date(value + dt.timedelta(days=direction))
        value = _walk(value, calendar, direction)
    return value
