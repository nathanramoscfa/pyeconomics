# tests/models/fixed_income/test_bond_pricing.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``fixed_income.bond_pricing``: its invariants, QuantLib as an oracle, refusals.

The oracle is QuantLib's ``FixedRateBond`` with ``BondFunctions``: clean price,
accrued amount and yield, under ACT/ACT (ICMA) and both 30/360 conventions,
compounded at the coupon frequency. That is the street convention; the treasury
convention is held to 31 CFR Part 356 Appendix B by the golden file.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import pytest
import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from fixed_income_draws import DAY_COUNTS, FREQUENCIES, bonds, qdate, quantlib_bond
from hypothesis import assume, given, reject, settings
from hypothesis import strategies as st

from pyeconomics.core import DomainError, InputError, run_model
from pyeconomics.models.fixed_income import bond_pricing

YIELDS = st.floats(min_value=-0.02, max_value=0.25)
CONVENTIONS = st.sampled_from(["street", "treasury"])


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(bond_pricing, inputs).outputs


def price(terms: dict[str, Any], y: float, convention: str = "street") -> Any:  # noqa: ANN401
    return run(
        calculation="price_from_yield",
        yield_to_maturity=y,
        convention=convention,
        **terms,
    )


@pytest.mark.invariant("fixed_income.bond_pricing", "price_decreases_with_yield")
@given(terms=bonds(), low=YIELDS, high=YIELDS, convention=CONVENTIONS)
def test_the_price_falls_as_the_yield_rises(
    terms: dict[str, Any], low: float, high: float, convention: str
) -> None:
    low, high = sorted((low, high))
    assume(high - low > 1e-6)
    at_low = price(terms, low, convention).full_price
    at_high = price(terms, high, convention).full_price
    assert at_high < at_low


@pytest.mark.invariant("fixed_income.bond_pricing", "par_bond_prices_at_par")
@given(
    terms=bonds(irregular=False, coupon=st.floats(min_value=0.0, max_value=0.3)),
    convention=CONVENTIONS,
)
def test_a_par_bond_prices_at_par_on_a_coupon_date(
    terms: dict[str, Any], convention: str
) -> None:
    # Move settlement back to the coupon date on or before it.
    on_date = {**terms, "settlement": _previous_coupon(terms)}
    result = price(on_date, terms["coupon_rate"], convention)
    assert math.isclose(result.full_price, 100.0, rel_tol=1e-12)
    assert result.accrued_interest == 0.0
    assert result.flat_price == result.full_price


def _previous_coupon(terms: dict[str, Any]) -> dt.date:
    months = (
        12
        // {"annual": 1, "semiannual": 2, "quarterly": 4, "monthly": 12}[
            terms["frequency"]
        ]
    )
    maturity, settlement = terms["maturity"], terms["settlement"]
    k = 0
    while True:
        k += 1
        year, month = divmod(maturity.year * 12 + maturity.month - 1 - k * months, 12)
        day = dt.date(year, month + 1, maturity.day)
        if day <= settlement:
            return day


@pytest.mark.invariant("fixed_income.bond_pricing", "full_equals_flat_plus_accrued")
@settings(deadline=None)  # the first yield solve imports SciPy
@given(terms=bonds(), y=YIELDS, convention=CONVENTIONS)
def test_the_full_price_is_flat_plus_accrued(
    terms: dict[str, Any], y: float, convention: str
) -> None:
    result = price(terms, y, convention)
    assert math.isclose(
        result.full_price,
        result.flat_price + result.accrued_interest,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
    back = run(
        calculation="yield_from_price",
        price=result.flat_price,
        convention=convention,
        **terms,
    )
    assume(result.flat_price > 0)
    assert math.isclose(back.full_price, result.full_price, rel_tol=1e-12)


@pytest.mark.invariant(
    "fixed_income.bond_pricing", "yield_to_worst_not_above_yield_to_maturity"
)
@settings(deadline=None)
@given(
    terms=bonds(max_years=30),
    y=st.floats(min_value=0.0, max_value=0.15),
    call_price=st.floats(min_value=100.0, max_value=110.0),
    data=st.data(),
)
def test_the_yield_to_worst_is_not_above_the_yield_to_maturity(
    terms: dict[str, Any], y: float, call_price: float, data: st.DataObject
) -> None:
    flat = price(terms, y).flat_price
    assume(flat > 1.0)
    dates = price(terms, y).next_coupon_date, terms["maturity"]
    calls = data.draw(st.lists(st.sampled_from(dates), min_size=1, max_size=2))
    try:
        result = run(
            calculation="yield_to_worst",
            price=flat,
            call_dates=calls,
            call_prices=[call_price] * len(calls),
            **terms,
        )
    except DomainError:
        reject()  # a call yields below -0.1, as the limitations say

    assert result.yield_to_worst <= result.yield_to_maturity
    assert math.isclose(result.yield_to_maturity, y, abs_tol=1e-9)


# --- QuantLib as an oracle -------------------------------------------------------


@pytest.mark.oracle("fixed_income.bond_pricing")
@settings(deadline=None)
@given(terms=bonds(), y=st.floats(min_value=-0.01, max_value=0.2))
def test_price_accrued_and_yield_agree_with_quantlib(
    terms: dict[str, Any], y: float
) -> None:
    result = price(terms, y)
    bond = quantlib_bond(terms)
    settlement = qdate(terms["settlement"])
    day_count = DAY_COUNTS[terms["day_count"]]
    frequency = FREQUENCIES[terms["frequency"]]
    accrued = ql.BondFunctions.accruedAmount(bond, settlement)
    clean = ql.BondFunctions.cleanPrice(
        bond, y, day_count, ql.Compounded, frequency, settlement
    )
    assert math.isclose(result.accrued_interest, accrued, abs_tol=1e-10)
    assert math.isclose(result.flat_price, clean, rel_tol=1e-11, abs_tol=1e-10)
    assume(clean > 1.0)
    solved = ql.BondFunctions.bondYield(
        bond,
        ql.BondPrice(clean, ql.BondPrice.Clean),
        day_count,
        ql.Compounded,
        frequency,
        settlement,
        1e-12,
        200,
    )
    ours = run(calculation="yield_from_price", price=clean, **terms)
    assert math.isclose(ours.yield_to_maturity, solved, abs_tol=1e-9)


@pytest.mark.oracle("fixed_income.bond_pricing")
def test_a_long_first_coupon_matches_quantlib() -> None:
    terms: dict[str, Any] = {
        "settlement": dt.date(1990, 6, 20),
        "maturity": dt.date(1995, 5, 15),
        "coupon_rate": 0.085,
        "issue_date": dt.date(1990, 3, 1),
        "first_period": "long",
    }
    result = price(terms, 0.0853)
    bond = quantlib_bond({**terms, "frequency": "semiannual"})
    clean = ql.BondFunctions.cleanPrice(
        bond,
        0.0853,
        DAY_COUNTS["act_act_icma"],
        ql.Compounded,
        ql.Semiannual,
        qdate(terms["settlement"]),
    )
    assert math.isclose(result.flat_price, clean, rel_tol=1e-12)
    assert math.isclose(bond.cashflows()[0].amount(), 100 * 0.085 / 2 * (1 + 75 / 181))


@pytest.mark.oracle("fixed_income.bond_pricing")
@pytest.mark.parametrize("day_count", ["thirty_360_us", "thirty_e_360"])
def test_settlement_on_the_31st_under_30_360_matches_quantlib(day_count: str) -> None:
    # 30/360 counts January 31 as the 30th: the time to the next coupon is the
    # period less the accrued part (344/360 under US rules), not a direct count
    # from settlement (345/360). A regression the duration oracle found.
    terms: dict[str, Any] = {
        "settlement": dt.date(1994, 1, 31),
        "maturity": dt.date(1995, 1, 15),
        "coupon_rate": 0.05,
        "frequency": "annual",
        "day_count": day_count,
    }
    result = price(terms, 0.06)
    clean = ql.BondFunctions.cleanPrice(
        quantlib_bond(terms),
        0.06,
        DAY_COUNTS[day_count],
        ql.Compounded,
        ql.Annual,
        qdate(terms["settlement"]),
    )
    assert math.isclose(result.flat_price, clean, rel_tol=1e-13)


# --- cases with exact answers and documented refusals ----------------------------


def test_a_call_yield_above_the_range_is_skipped_with_a_warning() -> None:
    result = run_model(
        bond_pricing,
        {
            "calculation": "yield_to_worst",
            "settlement": "2026-01-15",
            "maturity": "2036-01-15",
            "coupon_rate": 0.05,
            "price": 60.0,
            "call_dates": ["2026-07-15"],
            "call_prices": [100.0],
        },
    )
    assert result.outputs.worst_date == dt.date(2036, 1, 15)
    assert [w.code for w in result.warnings] == ["call_yield_above_range"]


def test_the_yield_to_call_equals_the_coupon_for_a_par_bond_callable_at_par() -> None:
    result = run(
        calculation="yield_to_call",
        settlement="2026-01-15",
        maturity="2036-01-15",
        coupon_rate=0.05,
        price=100.0,
        price_type="full",
        call_date="2031-01-15",
        call_price=100.0,
    )
    assert math.isclose(result.yield_to_call, 0.05, abs_tol=1e-12)


def test_an_issue_date_on_a_coupon_date_is_a_regular_schedule() -> None:
    bond = {"settlement": "2026-03-02", "maturity": "2036-01-15", "coupon_rate": 0.045}
    regular = price(bond, 0.05)
    for first_period in ("short", "long"):
        issued = price(
            {**bond, "issue_date": "2026-01-15", "first_period": first_period}, 0.05
        )
        assert issued == regular


def test_a_price_no_yield_gives_is_a_domain_error() -> None:
    with pytest.raises(DomainError, match="no yield"):
        run(
            calculation="yield_from_price",
            settlement="2026-01-15",
            maturity="2027-01-15",
            coupon_rate=0.05,
            price=500.0,
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"settlement": "2036-01-15"}, "before maturity"),
        ({"maturity": "2127-01-15"}, "100 years"),
        ({"issue_date": "2026-02-01"}, "issue date"),
        (
            {
                "issue_date": "2035-09-01",
                "settlement": "2035-10-01",
                "first_period": "long",
            },
            "long first period",
        ),
        (
            {
                "calculation": "yield_to_call",
                "price": 99.0,
                "call_price": 100.0,
                "call_date": "2030-03-01",
            },
            "coupon date",
        ),
        (
            {
                "calculation": "yield_to_worst",
                "price": 99.0,
                "call_prices": [100.0],
                "call_dates": ["2030-01-15", "2031-01-15"],
            },
            "one call price",
        ),
    ],
)
def test_inconsistent_terms_are_refused(change: dict[str, Any], message: str) -> None:
    inputs = {
        "calculation": "price_from_yield",
        "settlement": "2026-01-15",
        "maturity": "2036-01-15",
        "coupon_rate": 0.05,
        "yield_to_maturity": 0.05,
        **change,
    }
    if inputs["calculation"] != "price_from_yield":
        del inputs["yield_to_maturity"]
    with pytest.raises(InputError, match=message):
        run(**inputs)
