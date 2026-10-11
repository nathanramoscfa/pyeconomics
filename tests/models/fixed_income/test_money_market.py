# tests/models/fixed_income/test_money_market.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``fixed_income.money_market``: its invariants, and the cases it refuses."""

from __future__ import annotations

import math
from typing import Any

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from pyeconomics.core import DomainError, run_model
from pyeconomics.models.fixed_income import money_market

DAYS = st.integers(min_value=1, max_value=364)
POSITIVE_DISCOUNT = st.floats(min_value=1e-6, max_value=0.3)


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(money_market, inputs).outputs


@pytest.mark.invariant(
    "fixed_income.money_market", "discount_yield_below_investment_rate"
)
@given(discount=POSITIVE_DISCOUNT, days=DAYS, year=st.sampled_from([365, 366]))
def test_the_discount_rate_is_below_the_investment_rate(
    discount: float, days: int, year: int
) -> None:
    price = run(
        calculation="price_from_discount", discount_rate=discount, days=days
    ).price
    assume(price < 100.0)
    rate = run(
        calculation="investment_rate",
        price=price,
        days=days,
        days_in_year=year,
    ).investment_rate
    assert discount < rate


@pytest.mark.invariant(
    "fixed_income.money_market", "price_below_face_for_positive_yield"
)
@given(
    discount=POSITIVE_DISCOUNT,
    days=st.integers(min_value=1, max_value=730),
    face=st.floats(min_value=1.0, max_value=1e9),
)
def test_a_positive_discount_rate_prices_below_face(
    discount: float, days: int, face: float
) -> None:
    assume(discount * days < 360)
    price = run(
        calculation="price_from_discount",
        discount_rate=discount,
        days=days,
        face_value=face,
    ).price
    assert 0 < price < face


@pytest.mark.invariant("fixed_income.money_market", "price_yield_round_trip")
@given(
    discount=st.floats(min_value=-0.05, max_value=0.3),
    days=st.integers(min_value=1, max_value=730),
)
def test_the_discount_rate_of_its_price_is_the_rate(discount: float, days: int) -> None:
    assume(discount * days < 359)
    price = run(
        calculation="price_from_discount", discount_rate=discount, days=days
    ).price
    back = run(calculation="discount_from_price", price=price, days=days).discount_rate
    assert math.isclose(back, discount, rel_tol=1e-9, abs_tol=1e-12)


def test_the_two_investment_rate_formulas_meet_at_half_a_year() -> None:
    # At t = y/2 the quadratic's leading coefficient is zero and it is linear.
    short = run(calculation="investment_rate", price=98.0, days=182, days_in_year=365)
    over = run(calculation="investment_rate", price=98.0, days=183, days_in_year=366)
    at = run(calculation="investment_rate", price=98.0, days=183, days_in_year=365)
    assert math.isclose(over.investment_rate, 2 / 98 * 366 / 183, rel_tol=1e-12)
    assert at.investment_rate < short.investment_rate


def test_a_negative_yield_bill_prices_above_face() -> None:
    result = run(calculation="price_from_discount", discount_rate=-0.005, days=91)
    assert result.price > 100.0
    assert result.discount < 0


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        (
            {"calculation": "price_from_discount", "discount_rate": 1.0, "days": 360},
            "whole face",
        ),
        (
            {"calculation": "discount_from_price", "price": 1.0, "days": 1},
            "discount rate",
        ),
        (
            {"calculation": "money_market_yield", "price": 1.0, "days": 1},
            "money-market",
        ),
        (
            {"calculation": "investment_rate", "price": 1.0, "days": 10},
            "investment rate",
        ),
        (
            {"calculation": "investment_rate", "price": 1e9, "days": 300},
            "investment rate",
        ),
        (
            {"calculation": "effective_annual_yield", "price": 50.0, "days": 30},
            "exceeds",
        ),
        (
            {"calculation": "effective_annual_yield", "price": 1e6, "days": 30},
            "effective annual",
        ),
        (
            {
                "calculation": "holding_period_yield",
                "purchase_price": 1.0,
                "proceeds": 1e6,
            },
            "holding-period",
        ),
    ],
)
def test_out_of_range_results_are_domain_errors(
    inputs: dict[str, Any], message: str
) -> None:
    with pytest.raises(DomainError, match=message):
        run(**inputs)
