# tests/unit/core/test_daycount.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Cited recomputations and independent QuantLib day-count comparisons."""

from __future__ import annotations

import datetime as dt
from functools import partial

import pytest
import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import DayCount, Frequency, InputError, add_months, year_fraction

DATES = st.dates(min_value=dt.date(1950, 1, 1), max_value=dt.date(2150, 12, 31))
ORACLES = {
    DayCount.THIRTY_360_US: ql.Thirty360(ql.Thirty360.USA),
    DayCount.THIRTY_E_360: ql.Thirty360(ql.Thirty360.European),
    DayCount.ACT_360: ql.Actual360(),
    DayCount.ACT_365_FIXED: ql.Actual365Fixed(),
    DayCount.ACT_ACT_ISDA: ql.ActualActual(ql.ActualActual.ISDA),
    DayCount.ACT_ACT_ICMA: ql.ActualActual(ql.ActualActual.ISMA),
}


def qdate(value: dt.date) -> ql.Date:
    return ql.Date(value.day, value.month, value.year)


def test_closed_vocabulary() -> None:
    assert set(DayCount.__members__) == {
        "THIRTY_360_US",
        "THIRTY_E_360",
        "ACT_360",
        "ACT_365_FIXED",
        "ACT_ACT_ISDA",
        "ACT_ACT_ICMA",
    }


# ISDA, EMU and Market Conventions: Recent Developments (November 1998),
# Actual/Actual examples: first example, short first (two periods), long
# first (two periods), short final (two periods). Original memo:
# https://www.isda.org/a/AIJEE/1998-ISDA-memo-EMU-and-Market-Conventions-Recent-Developments.pdf
# Date inputs independently confirmed in QuantLib test-suite/daycounters.cpp,
# testActualActual. Fractions below are recomputed from day counts, not the
# memo's rounded decimals. The second long-first ISDA value uses calendar-year
# splitting (QuantLib explicitly flags the memo's disagreement).
@pytest.mark.parametrize(
    ("start", "end", "ref_start", "ref_end", "frequency", "isda", "icma"),
    [
        (
            "2003-11-01",
            "2004-05-01",
            "2003-11-01",
            "2004-05-01",
            Frequency.SEMIANNUAL,
            61 / 365 + 121 / 366,
            0.5,
        ),
        (
            "1999-02-01",
            "1999-07-01",
            "1998-07-01",
            "1999-07-01",
            Frequency.ANNUAL,
            150 / 365,
            150 / 365,
        ),
        (
            "1999-07-01",
            "2000-07-01",
            "1999-07-01",
            "2000-07-01",
            Frequency.ANNUAL,
            184 / 365 + 182 / 366,
            1.0,
        ),
        (
            "2002-08-15",
            "2003-07-15",
            "2003-01-15",
            "2003-07-15",
            Frequency.SEMIANNUAL,
            334 / 365,
            153 / (184 * 2) + 0.5,
        ),
        (
            "2003-07-15",
            "2004-01-15",
            "2003-07-15",
            "2004-01-15",
            Frequency.SEMIANNUAL,
            170 / 365 + 14 / 366,
            0.5,
        ),
        (
            "1999-07-30",
            "2000-01-30",
            "1999-07-30",
            "2000-01-30",
            Frequency.SEMIANNUAL,
            155 / 365 + 29 / 366,
            0.5,
        ),
        (
            "2000-01-30",
            "2000-06-30",
            "2000-01-30",
            "2000-07-30",
            Frequency.SEMIANNUAL,
            152 / 366,
            152 / (182 * 2),
        ),
    ],
)
def test_isda_worked_examples(  # noqa: PLR0913, PLR0917 - cited case columns
    start: str,
    end: str,
    ref_start: str,
    ref_end: str,
    frequency: Frequency,
    isda: float,
    icma: float,
) -> None:
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    assert year_fraction(first, last, DayCount.ACT_ACT_ISDA) == pytest.approx(
        isda, abs=1e-14, rel=0
    )
    assert year_fraction(
        first,
        last,
        DayCount.ACT_ACT_ICMA,
        reference_start=dt.date.fromisoformat(ref_start),
        reference_end=dt.date.fromisoformat(ref_end),
        frequency=frequency,
    ) == pytest.approx(icma, abs=1e-14, rel=0)


# QuantLib Thirty360::USA, ql/time/daycounters/thirty360.cpp USA_Impl::dayCount;
# European: 2006 ISDA Definitions section 4.16. Hand-computed rule cases,
# covering both February ends, a sole February end, and 31st adjustment.
@pytest.mark.parametrize(
    ("start", "end", "us_days", "e_days"),
    [
        ("2023-02-28", "2023-03-31", 30, 32),
        ("2024-02-29", "2024-03-31", 30, 31),
        ("2023-02-28", "2024-02-29", 360, 361),
        ("2024-02-29", "2025-02-28", 360, 359),
        ("2024-01-31", "2024-02-29", 29, 29),
        ("2024-01-30", "2024-03-31", 60, 60),
        ("2024-01-29", "2024-03-31", 62, 61),
        ("2024-01-31", "2024-04-30", 90, 90),
        ("2024-02-28", "2024-03-31", 33, 32),
    ],
)
def test_thirty_360_worked_rules(
    start: str, end: str, us_days: int, e_days: int
) -> None:
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    for convention, expected in [
        (DayCount.THIRTY_360_US, us_days),
        (DayCount.THIRTY_E_360, e_days),
    ]:
        assert year_fraction(first, last, convention) == expected / 360
        assert year_fraction(last, first, convention) == -expected / 360


@pytest.mark.parametrize("convention", [DayCount.ACT_360, DayCount.ACT_365_FIXED])
def test_actual_worked_examples(convention: DayCount) -> None:
    # ISDA 2006 section 4.16: actual calendar days divided by the fixed basis.
    denominator = 360 if convention is DayCount.ACT_360 else 365
    assert (
        year_fraction(dt.date(2024, 2, 28), dt.date(2024, 3, 1), convention)
        == 2 / denominator
    )
    assert (
        year_fraction(dt.date(2023, 2, 28), dt.date(2023, 3, 1), convention)
        == 1 / denominator
    )


@pytest.mark.parametrize(
    "convention", [c for c in DayCount if c is not DayCount.ACT_ACT_ICMA]
)
@given(DATES, DATES)
def test_generated_pairs_against_quantlib(
    convention: DayCount, first: dt.date, last: dt.date
) -> None:
    low, high = sorted((first, last))
    expected = ORACLES[convention].yearFraction(qdate(low), qdate(high))
    sign = 1 if first <= last else -1
    assert year_fraction(first, last, convention) == pytest.approx(
        sign * expected, abs=1e-14, rel=0
    )
    assert year_fraction(first, first, convention) == 0.0


@given(
    DATES,
    st.sampled_from(
        [Frequency.ANNUAL, Frequency.SEMIANNUAL, Frequency.QUARTERLY, Frequency.MONTHLY]
    ),
    st.integers(-700, 700),
    st.integers(0, 700),
)
def test_icma_generated_irregular_pairs(
    anchor: dt.date, frequency: Frequency, before: int, duration: int
) -> None:
    ref_end = add_months(anchor, 12 // frequency.periods_per_year)
    first = anchor + dt.timedelta(days=before)
    last = first + dt.timedelta(days=duration)
    # QuantLib's explicit-reference overload requires first < reference_end.
    # Shift the anchor forward for long first periods; bound the generated
    # horizon so every date stays inside the requested 1950-2150 oracle range.
    if first >= ref_end or first < dt.date(1950, 1, 1) or last > dt.date(2150, 12, 31):
        return
    if first < anchor and last > ref_end:
        return  # QuantLib rejects a period straddling both reference ends.
    calculate = partial(
        year_fraction,
        convention=DayCount.ACT_ACT_ICMA,
        reference_start=anchor,
        reference_end=ref_end,
        frequency=frequency,
    )
    expected = ORACLES[DayCount.ACT_ACT_ICMA].yearFraction(
        qdate(first), qdate(last), qdate(anchor), qdate(ref_end)
    )
    assert calculate(first, last) == pytest.approx(expected, abs=1e-14, rel=0)
    assert calculate(last, first) == pytest.approx(-expected, abs=1e-14, rel=0)
    assert calculate(first, first) == 0.0


@pytest.mark.parametrize(
    "convention", [DayCount.ACT_360, DayCount.ACT_365_FIXED, DayCount.ACT_ACT_ISDA]
)
@given(DATES, DATES, DATES)
def test_additivity(
    convention: DayCount, first: dt.date, middle: dt.date, last: dt.date
) -> None:
    first, middle, last = sorted((first, middle, last))
    assert year_fraction(first, last, convention) == pytest.approx(
        year_fraction(first, middle, convention)
        + year_fraction(middle, last, convention),
        abs=1e-13,
        rel=0,
    )


def test_icma_requires_consistent_references_even_for_equal_dates() -> None:
    first, last = dt.date(2024, 1, 1), dt.date(2024, 7, 1)
    with pytest.raises(InputError, match="requires"):
        year_fraction(first, first, DayCount.ACT_ACT_ICMA)
    for frequency in [Frequency.DAILY, Frequency.WEEKLY]:
        with pytest.raises(InputError, match="frequency"):
            year_fraction(
                first,
                last,
                DayCount.ACT_ACT_ICMA,
                reference_start=first,
                reference_end=last,
                frequency=frequency,
            )
    with pytest.raises(InputError, match="regular coupon"):
        year_fraction(
            first,
            last,
            DayCount.ACT_ACT_ICMA,
            reference_start=last,
            reference_end=first,
            frequency=Frequency.SEMIANNUAL,
        )
    with pytest.raises(InputError, match="regular coupon"):
        year_fraction(
            first,
            last,
            DayCount.ACT_ACT_ICMA,
            reference_start=first,
            reference_end=last,
            frequency=Frequency.MONTHLY,
        )
    with pytest.raises(InputError, match="DayCount"):
        year_fraction(first, last, "act_360")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type] - deliberate invalid input


@pytest.mark.parametrize(
    "convention", [c for c in DayCount if c is not DayCount.ACT_ACT_ICMA]
)
def test_unused_reference_arguments_are_rejected(convention: DayCount) -> None:
    first, last = dt.date(2024, 1, 1), dt.date(2024, 7, 1)
    with pytest.raises(InputError, match="takes no reference"):
        year_fraction(first, last, convention, reference_start=first)
    with pytest.raises(InputError, match="takes no reference"):
        year_fraction(first, last, convention, frequency=Frequency.SEMIANNUAL)


def test_icma_clamped_backward_reference_regression() -> None:
    # QuantLib explicit-reference ISMA steps backwards through February before
    # constructing earlier notional periods (ActualActual::Old_ISMA_Impl).
    assert year_fraction(
        dt.date(2000, 2, 28),
        dt.date(2000, 2, 29),
        DayCount.ACT_ACT_ICMA,
        reference_start=dt.date(2000, 8, 30),
        reference_end=dt.date(2001, 2, 28),
        frequency=Frequency.SEMIANNUAL,
    ) == 1 / (184 * 2)
