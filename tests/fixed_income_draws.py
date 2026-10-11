# tests/fixed_income_draws.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Bond draws for the fixed-income property tests, and the same bonds in QuantLib.

:func:`bonds` draws the terms of a fixed-coupon bond as a mapping the
``fixed_income`` models accept: dates on the 15th (so no month-end rule is in
play and QuantLib's 30/360 coupons are c/f too), a regular schedule or an
irregular first period, and a coupon rate. :func:`quantlib_bond` builds the
same bond as a QuantLib ``FixedRateBond`` with a face value of 100, the oracle
the price, yield, accrued interest, duration and convexity tests compare with.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Final

import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from hypothesis import strategies as st

__all__ = ["DAY_COUNTS", "FREQUENCIES", "bonds", "qdate", "quantlib_bond"]

FREQUENCIES: Final = {
    "annual": ql.Annual,
    "semiannual": ql.Semiannual,
    "quarterly": ql.Quarterly,
    "monthly": ql.Monthly,
}
DAY_COUNTS: Final = {
    "act_act_icma": ql.ActualActual(ql.ActualActual.ISMA),
    "thirty_360_us": ql.Thirty360(ql.Thirty360.USA),
    "thirty_e_360": ql.Thirty360(ql.Thirty360.European),
}
_MONTHS: Final = {"annual": 12, "semiannual": 6, "quarterly": 3, "monthly": 1}


def qdate(value: dt.date) -> ql.Date:
    return ql.Date(value.day, value.month, value.year)


def _shift(value: dt.date, months: int) -> dt.date:
    year, month = divmod(value.year * 12 + value.month - 1 + months, 12)
    return dt.date(year, month + 1, value.day)


@st.composite
def bonds(
    draw: st.DrawFn,
    *,
    max_years: int = 40,
    irregular: bool = True,
    coupon: st.SearchStrategy[float] | None = None,
) -> dict[str, Any]:
    """Draw a bond's terms; settlement is between coupon dates or on one."""
    frequency = draw(st.sampled_from(list(FREQUENCIES)))
    months = _MONTHS[frequency]
    maturity = dt.date(
        draw(st.integers(min_value=1995, max_value=2150)),
        draw(st.integers(min_value=1, max_value=12)),
        15,
    )
    periods = draw(st.integers(min_value=1, max_value=max_years * 12 // months))
    previous = _shift(maturity, -periods * months)
    into = draw(st.integers(min_value=0, max_value=27 * months))
    settlement = previous + dt.timedelta(days=into)
    terms: dict[str, Any] = {
        "settlement": settlement,
        "maturity": maturity,
        "coupon_rate": draw(
            coupon if coupon is not None else st.floats(min_value=0.0, max_value=0.15)
        ),
        "frequency": frequency,
        "day_count": draw(st.sampled_from(list(DAY_COUNTS))),
    }
    if irregular and draw(st.booleans()):
        # Issued in the period before settlement's or in settlement's, never on
        # a coupon date (those fall on the 15th), so the first period is a stub.
        prior = _shift(maturity, -(periods + 1) * months)
        span = (settlement - prior).days
        issue = prior + dt.timedelta(
            days=draw(st.integers(min_value=1, max_value=span))
        )
        if issue.day != 15:
            # A long first period needs a regular period after the stub.
            long_first = (issue < previous or periods >= 2) and draw(st.booleans())
            terms["issue_date"] = issue
            terms["first_period"] = "long" if long_first else "short"
    return terms


def quantlib_bond(terms: dict[str, Any]) -> ql.FixedRateBond:
    """Build the same bond in QuantLib, with a face value of 100."""
    frequency = terms.get("frequency", "semiannual")
    tenor = ql.Period(FREQUENCIES[frequency])
    maturity = qdate(terms["maturity"])
    issue = terms.get("issue_date")
    first = ql.Date()
    if issue is None:
        # Any start a year before settlement: the stub it makes has ended.
        effective = qdate(terms["settlement"]) - ql.Period(1, ql.Years)
    else:
        effective = qdate(issue)
        if terms.get("first_period") == "long":
            regular = ql.Schedule(
                effective,
                maturity,
                tenor,
                ql.NullCalendar(),
                ql.Unadjusted,
                ql.Unadjusted,
                ql.DateGeneration.Backward,
                False,  # noqa: FBT003 - QuantLib's positional end-of-month flag
            )
            # The first coupon of a long first period is the regular schedule's
            # second date after the stub.
            dates = [regular[i] for i in range(len(regular))]
            if len(dates) > 2 and dates[1] != effective:
                first = dates[2]
    schedule = ql.Schedule(
        effective,
        maturity,
        tenor,
        ql.NullCalendar(),
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False,  # noqa: FBT003 - QuantLib's positional end-of-month flag
        first,
    )
    day_count = DAY_COUNTS[terms.get("day_count", "act_act_icma")]
    return ql.FixedRateBond(
        0,
        100.0,
        schedule,
        [terms["coupon_rate"]],
        day_count,
        ql.Unadjusted,
        terms.get("redemption", 100.0),
    )
