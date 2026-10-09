# tests/unit/core/test_schedule.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Coupon schedules against QuantLib's backward Schedule construction."""

from __future__ import annotations

import datetime as dt
from itertools import pairwise
from typing import Literal

import pytest
import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import (
    BusinessDayConvention,
    Frequency,
    InputError,
    add_months,
    generate,
    is_business_day,
)

TENORS = {
    Frequency.ANNUAL: ql.Period(12, ql.Months),
    Frequency.SEMIANNUAL: ql.Period(6, ql.Months),
    Frequency.QUARTERLY: ql.Period(3, ql.Months),
    Frequency.MONTHLY: ql.Period(1, ql.Months),
    Frequency.WEEKLY: ql.Period(1, ql.Weeks),
    Frequency.DAILY: ql.Period(1, ql.Days),
}


def qdate(value: dt.date) -> ql.Date:
    return ql.Date(value.day, value.month, value.year)


def compare(
    effective: dt.date,
    maturity: dt.date,
    frequency: Frequency,
    stub: Literal["short_front", "long_front"],
    *,
    eom: bool,
) -> None:
    short = ql.Schedule(
        qdate(effective),
        qdate(maturity),
        TENORS[frequency],
        ql.NullCalendar(),
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        eom,
    )
    # QuantLib expresses a long front stub as an explicit firstDate equal
    # to the second regular coupon. This keeps the oracle independent of our
    # schedule arithmetic.
    first_coupon = ql.Date()
    if stub == "long_front" and not short.isRegular(1):
        first_coupon = short[2]
    expected = ql.Schedule(
        qdate(effective),
        qdate(maturity),
        TENORS[frequency],
        ql.NullCalendar(),
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        eom,
        first_coupon,
    )
    actual = generate(effective, maturity, frequency, stub=stub, end_of_month=eom)
    assert [d.isoformat() for d in actual.accrual_dates] == [d.ISO() for d in expected]
    assert actual.payment_dates == actual.accrual_dates[1:]


@pytest.mark.parametrize("frequency", list(Frequency))
@pytest.mark.parametrize("stub", ["short_front", "long_front"])
@pytest.mark.parametrize("eom", [False, True])
@pytest.mark.parametrize(
    ("effective", "maturity"),
    [
        (dt.date(2020, 2, 29), dt.date(2025, 2, 28)),
        (dt.date(2020, 1, 15), dt.date(2025, 1, 31)),
        (dt.date(2020, 1, 31), dt.date(2025, 1, 31)),
        (dt.date(2020, 2, 15), dt.date(2025, 8, 30)),
    ],
)
def test_schedule_oracle(
    frequency: Frequency,
    stub: Literal["short_front", "long_front"],
    *,
    eom: bool,
    effective: dt.date,
    maturity: dt.date,
) -> None:
    compare(effective, maturity, frequency, stub, eom=eom)


@given(
    maturity=st.dates(min_value=dt.date(1955, 1, 1), max_value=dt.date(2145, 12, 31)),
    frequency=st.sampled_from(
        [Frequency.ANNUAL, Frequency.SEMIANNUAL, Frequency.QUARTERLY, Frequency.MONTHLY]
    ),
    eom=st.booleans(),
    extra_days=st.integers(0, 20),
)
def test_generated_schedules(
    maturity: dt.date, frequency: Frequency, *, eom: bool, extra_days: int
) -> None:
    effective = add_months(maturity, -36) - dt.timedelta(days=extra_days)
    for stub in ("short_front", "long_front"):
        compare(effective, maturity, frequency, stub, eom=eom)


def test_adjustment_preserves_accruals() -> None:
    unadjusted = generate(
        dt.date(2023, 12, 31),
        dt.date(2025, 12, 31),
        Frequency.QUARTERLY,
        end_of_month=True,
    )
    adjusted = generate(
        dt.date(2023, 12, 31),
        dt.date(2025, 12, 31),
        Frequency.QUARTERLY,
        end_of_month=True,
        calendar="target2",
        convention=BusinessDayConvention.MODIFIED_FOLLOWING,
    )
    assert adjusted.accrual_dates == unadjusted.accrual_dates
    assert len(adjusted.payment_dates) == len(adjusted.accrual_dates) - 1
    assert all(is_business_day(day, "target2") for day in adjusted.payment_dates)
    end_of_month = True
    oracle = ql.Schedule(
        ql.Date(31, 12, 2023),
        ql.Date(31, 12, 2025),
        ql.Period(3, ql.Months),
        ql.TARGET(),
        ql.ModifiedFollowing,
        ql.ModifiedFollowing,
        ql.DateGeneration.Backward,
        end_of_month,
    )
    assert [day.isoformat() for day in adjusted.payment_dates] == [
        oracle[i].ISO() for i in range(1, len(oracle))
    ]
    for left, right in pairwise(adjusted.accrual_dates):
        assert add_months(left, 3, end_of_month=True) == right


@pytest.mark.parametrize(
    ("effective", "maturity", "stub"),
    [
        ("2024-01-01", "2024-01-01", "short_front"),
        ("2025-01-01", "2024-01-01", "short_front"),
        ("2024-01-01", "2024-02-01", "short_front"),
        ("2024-01-01", "2024-09-01", "long_front"),
    ],
)
def test_invalid_schedule(
    effective: str, maturity: str, stub: Literal["short_front", "long_front"]
) -> None:
    with pytest.raises(InputError):
        generate(
            dt.date.fromisoformat(effective),
            dt.date.fromisoformat(maturity),
            Frequency.SEMIANNUAL,
            stub=stub,
            end_of_month=False,
        )


def test_bad_options_and_too_many_dates() -> None:
    first, last = dt.date(1900, 1, 1), dt.date(2200, 12, 31)
    with pytest.raises(InputError, match="MAX_ARRAY_LENGTH"):
        generate(first, last, Frequency.DAILY, end_of_month=False)
    with pytest.raises(InputError, match="Frequency"):
        generate(first, last, "monthly", end_of_month=False)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type] - deliberate invalid input
    with pytest.raises(InputError, match="stub"):
        generate(first, last, Frequency.ANNUAL, stub="short_back", end_of_month=False)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type] - deliberate invalid input
    result = generate(first, last, Frequency.ANNUAL, end_of_month=True)
    assert result.accrual_dates[0] == first
    assert result.accrual_dates[-1] == last
