# tests/unit/core/test_calendars.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Exhaustive 2000-2030 calendar parity, adjustments and signed advances."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import (
    CALENDAR_IDS,
    BusinessDayConvention,
    CalendarId,
    InputError,
    add_business_days,
    adjust,
    is_business_day,
)

ORACLES = {
    "weekends_only": ql.WeekendsOnly(),
    "us_federal": ql.UnitedStates(ql.UnitedStates.Settlement),
    "us_nyse": ql.UnitedStates(ql.UnitedStates.NYSE),
    "target2": ql.TARGET(),
    "uk_england": ql.UnitedKingdom(ql.UnitedKingdom.Settlement),
}
CONVENTIONS = {
    BusinessDayConvention.UNADJUSTED: ql.Unadjusted,
    BusinessDayConvention.FOLLOWING: ql.Following,
    BusinessDayConvention.MODIFIED_FOLLOWING: ql.ModifiedFollowing,
    BusinessDayConvention.PRECEDING: ql.Preceding,
    BusinessDayConvention.MODIFIED_PRECEDING: ql.ModifiedPreceding,
}

# OPM memorandum of June 17, 2021, Juneteenth National Independence Day Holiday,
# paragraph beginning "For employees with a Monday-through-Friday work schedule":
# https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/juneteenth-national-independence-day-holiday.pdf
# June 18, 2021 was the federal observed holiday. holidays US includes it;
# QuantLib 1.43 Settlement applies Juneteenth only from 2022 (isJuneteenth in
# ql/time/calendars/unitedstates.cpp). Keep the federal calendar's sourced rule.
# Store expected booleans on BOTH sides, and assert the exact set of differences
# so stale exceptions cannot silently hide a future provider/oracle correction.
DIFFERENCES = {"us_federal": {dt.date(2021, 6, 18): (False, True)}}


def qdate(value: dt.date) -> ql.Date:
    return ql.Date(value.day, value.month, value.year)


def test_closed_vocabulary() -> None:
    assert set(BusinessDayConvention.__members__) == {
        "UNADJUSTED",
        "FOLLOWING",
        "MODIFIED_FOLLOWING",
        "PRECEDING",
        "MODIFIED_PRECEDING",
    }
    assert set(CALENDAR_IDS) == set(ORACLES)


@pytest.mark.parametrize("calendar", CALENDAR_IDS)
def test_every_business_day_2000_through_2030(calendar: CalendarId) -> None:
    day = dt.date(2000, 1, 1)
    differences: dict[dt.date, tuple[bool, bool]] = {}
    while day < dt.date(2031, 1, 1):
        ours = is_business_day(day, calendar)
        theirs = bool(ORACLES[calendar].isBusinessDay(qdate(day)))
        if ours != theirs:
            differences[day] = (ours, theirs)
        day += dt.timedelta(days=1)
    assert differences == DIFFERENCES.get(calendar, {})


@pytest.mark.parametrize("calendar", CALENDAR_IDS)
@pytest.mark.parametrize("convention", list(BusinessDayConvention))
@pytest.mark.parametrize(
    "day",
    [
        dt.date(2024, 3, 31),
        dt.date(2024, 9, 1),
        dt.date(2024, 12, 25),
        dt.date(2024, 1, 2),
    ],
)
def test_adjustment_against_quantlib(
    calendar: CalendarId, convention: BusinessDayConvention, day: dt.date
) -> None:
    expected = ORACLES[calendar].adjust(qdate(day), CONVENTIONS[convention]).ISO()
    result = adjust(day, calendar, convention)
    assert result.isoformat() == expected
    if convention is not BusinessDayConvention.UNADJUSTED:
        assert is_business_day(result, calendar)


@given(
    st.dates(min_value=dt.date(2002, 1, 1), max_value=dt.date(2030, 1, 1)),
    st.integers(-30, 30),
    st.sampled_from(CALENDAR_IDS),
)
def test_signed_advance_against_quantlib(
    day: dt.date, offset: int, calendar: CalendarId
) -> None:
    # Exclude the sole documented provider/oracle difference from an advance
    # that could cross it; the exhaustive calendar test above still covers it.
    if calendar == "us_federal" and dt.date(2021, 5, 1) <= day <= dt.date(2021, 8, 1):
        return
    result = add_business_days(day, offset, calendar)
    expected = ORACLES[calendar].advance(qdate(day), offset, ql.Days).ISO()
    assert result.isoformat() == expected
    assert is_business_day(result, calendar)


def test_december_observance_from_next_year() -> None:
    assert not is_business_day(dt.date(2021, 12, 31), "us_federal")
    assert is_business_day(dt.date(2021, 12, 31), "us_nyse")


def test_invalid_arguments() -> None:
    day = dt.date(2024, 1, 1)
    with pytest.raises(InputError, match="unknown calendar"):
        is_business_day(day, "sifma")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type] - deliberate invalid input
    with pytest.raises(InputError, match="explicit calendar"):
        adjust(day, convention=BusinessDayConvention.FOLLOWING)
    with pytest.raises(InputError, match="BusinessDayConvention"):
        adjust(day, "target2", "following")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type] - deliberate invalid input
    assert adjust(day) == day


@pytest.mark.parametrize("offset", [True, 0.5, "2", None])
def test_invalid_offset(offset: Any) -> None:  # noqa: ANN401 - invalid inputs
    with pytest.raises(InputError, match="integer"):
        add_business_days(dt.date(2024, 1, 1), offset, "target2")


def test_date_boundaries() -> None:
    with pytest.raises(InputError, match="between"):
        add_business_days(dt.date(1900, 1, 1), -1, "weekends_only")
    with pytest.raises(InputError, match="between"):
        add_business_days(dt.date(2200, 12, 31), 1, "weekends_only")
    # 2200-12-31 is Wednesday, so the upper bound itself is a business day.
    assert adjust(
        dt.date(2200, 12, 31), "weekends_only", BusinessDayConvention.FOLLOWING
    ) == dt.date(2200, 12, 31)


@pytest.mark.parametrize("calendar", [c for c in CALENDAR_IDS if c != "weekends_only"])
def test_provider_year_limits_fail_closed(calendar: CalendarId) -> None:
    # HolidayBase._populate silently returns outside start_year/end_year:
    # https://holidays.readthedocs.io/en/latest/api/#holidays.holiday_base.HolidayBase
    with pytest.raises(InputError, match="supports years"):
        is_business_day(dt.date(2101, 1, 1), calendar)
    with pytest.raises(InputError, match="supports years"):
        is_business_day(dt.date(2101, 1, 2), calendar)
    assert not is_business_day(dt.date(2100, 1, 1), calendar)


def test_target_did_not_exist_before_1999() -> None:
    with pytest.raises(InputError, match="supports years 1999-2100"):
        is_business_day(dt.date(1998, 12, 31), "target2")
    assert not is_business_day(dt.date(1999, 1, 1), "target2")
