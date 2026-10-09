# tests/unit/core/test_dates.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Bounded date arithmetic, clamping and end-of-month rules."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import (
    InputError,
    actual_days,
    add_months,
    add_years,
    is_end_of_month,
    validate_date,
)


@pytest.mark.parametrize(
    ("value", "months", "eom", "expected"),
    [
        (dt.date(2024, 1, 31), 1, False, dt.date(2024, 2, 29)),
        (dt.date(2023, 1, 31), 1, False, dt.date(2023, 2, 28)),
        (dt.date(2024, 2, 29), 1, True, dt.date(2024, 3, 31)),
        (dt.date(2024, 2, 29), 1, False, dt.date(2024, 3, 29)),
        (dt.date(2024, 3, 31), -1, True, dt.date(2024, 2, 29)),
        (dt.date(2024, 1, 15), -13, True, dt.date(2022, 12, 15)),
        (dt.date(1900, 1, 1), 0, False, dt.date(1900, 1, 1)),
        (dt.date(2200, 12, 31), 0, True, dt.date(2200, 12, 31)),
    ],
)
def test_month_shifts(
    value: dt.date, months: int, *, eom: bool, expected: dt.date
) -> None:
    assert add_months(value, months, end_of_month=eom) == expected


def test_year_shifts_and_actual_days() -> None:
    leap = dt.date(2024, 2, 29)
    assert add_years(leap, 1) == dt.date(2025, 2, 28)
    assert add_years(dt.date(2023, 2, 28), 1, end_of_month=True) == leap
    assert actual_days(dt.date(2024, 2, 28), dt.date(2024, 3, 1)) == 2
    assert actual_days(dt.date(2024, 3, 1), dt.date(2024, 2, 28)) == -2
    assert is_end_of_month(leap)
    assert not is_end_of_month(dt.date(2024, 2, 28))


@pytest.mark.parametrize(
    "value", [None, "2024-01-01", dt.datetime(2024, 1, 1, tzinfo=dt.UTC)]
)
def test_refuse_non_dates(value: object) -> None:
    with pytest.raises(InputError, match="calendar date"):
        validate_date(value)


@pytest.mark.parametrize("value", [dt.date(1899, 12, 31), dt.date(2201, 1, 1)])
def test_bounds(value: dt.date) -> None:
    with pytest.raises(InputError, match="between"):
        actual_days(value, dt.date(2000, 1, 1))
    with pytest.raises(InputError, match="between"):
        is_end_of_month(value)


@pytest.mark.parametrize("months", [-1201, 2412, 10**30])
def test_result_bounds(months: int) -> None:
    with pytest.raises(InputError, match="result"):
        add_months(dt.date(2000, 1, 1), months)


@pytest.mark.parametrize("offset", [True, 0.5, None, "2"])
def test_offset_types(offset: Any) -> None:  # noqa: ANN401 - invalid inputs
    with pytest.raises(InputError, match="integer"):
        add_months(dt.date(2000, 1, 1), offset)
    with pytest.raises(InputError, match="integer"):
        add_years(dt.date(2000, 1, 1), offset)


@given(
    st.dates(min_value=dt.date(1950, 1, 1), max_value=dt.date(2150, 12, 28)).filter(
        lambda day: day.day <= 28
    ),
    st.integers(-120, 120),
)
def test_month_round_trip(value: dt.date, months: int) -> None:
    assert add_months(add_months(value, months), -months) == value
