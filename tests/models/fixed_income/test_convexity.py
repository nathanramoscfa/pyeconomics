# tests/models/fixed_income/test_convexity.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``fixed_income.convexity``: its invariants, QuantLib as an oracle, refusals.

The oracle is QuantLib's ``BondFunctions.convexity`` on the same bond, at the
same yield compounded at the coupon frequency.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import pytest
import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from fixed_income_draws import DAY_COUNTS, FREQUENCIES, bonds, qdate, quantlib_bond
from hypothesis import assume, given
from hypothesis import strategies as st

from pyeconomics.core import run_model
from pyeconomics.models.fixed_income import convexity

YIELDS = st.floats(min_value=-0.02, max_value=0.25)
PERIODS = {"annual": 1, "semiannual": 2, "quarterly": 4, "monthly": 12}


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(convexity, inputs).outputs


@pytest.mark.invariant(
    "fixed_income.convexity", "convexity_positive_for_option_free_bonds"
)
@given(terms=bonds(), y=YIELDS, rate=st.floats(min_value=-0.02, max_value=0.2))
def test_convexity_is_positive(terms: dict[str, Any], y: float, rate: float) -> None:
    assert run(calculation="analytical", yield_to_maturity=y, **terms).convexity > 0
    effective = run(
        calculation="effective",
        curve_tenors=[1.0],
        curve_rates=[rate],
        bump=0.001,
        **terms,
    ).effective_convexity
    assert effective > 0


@pytest.mark.invariant("fixed_income.convexity", "approximation_error_is_third_order")
@given(
    terms=bonds(max_years=30),
    y=st.floats(min_value=0.0, max_value=0.15),
    change=st.floats(min_value=0.002, max_value=0.02),
    sign=st.sampled_from([-1.0, 1.0]),
)
def test_halving_the_yield_change_cuts_the_error_about_eightfold(
    terms: dict[str, Any], y: float, change: float, sign: float
) -> None:
    def error(dy: float) -> float:
        return float(
            run(
                calculation="price_change",
                yield_to_maturity=y,
                yield_change=dy,
                **terms,
            ).approximation_error
        )

    full, half = error(sign * change), error(sign * change / 2)
    assume(abs(full) > 1e-11)  # above rounding in the repriced change
    # The error is c3 dy^3 + c4 dy^4 + ...: halving dy divides it by 8 to
    # within the fourth-order term, which the bound on dy keeps below a half.
    assert 4 < full / half < 16


@pytest.mark.invariant("fixed_income.convexity", "zero_coupon_closed_form")
@given(
    periods=st.integers(min_value=1, max_value=400),
    frequency=st.sampled_from(list(PERIODS)),
    y=YIELDS,
)
def test_a_zero_coupon_bond_has_its_closed_form(
    periods: int, frequency: str, y: float
) -> None:
    f = PERIODS[frequency]
    assume(periods <= 100 * f)  # at most 100 years to maturity
    maturity = dt.date(2120, 6, 15)
    year, month = divmod(
        maturity.year * 12 + maturity.month - 1 - periods * 12 // f, 12
    )
    result = run(
        calculation="analytical",
        settlement=dt.date(year, month + 1, 15),
        maturity=maturity,
        coupon_rate=0.0,
        frequency=frequency,
        yield_to_maturity=y,
    )
    expected = periods * (periods + 1) / (f * f * (1 + y / f) ** 2)
    assert math.isclose(result.convexity, expected, rel_tol=1e-13)


# --- QuantLib as an oracle -------------------------------------------------------


@pytest.mark.oracle("fixed_income.convexity")
@given(terms=bonds(), y=st.floats(min_value=-0.01, max_value=0.2))
def test_convexity_agrees_with_quantlib(terms: dict[str, Any], y: float) -> None:
    result = run(calculation="analytical", yield_to_maturity=y, **terms)
    rate = ql.InterestRate(
        y,
        DAY_COUNTS[terms["day_count"]],
        ql.Compounded,
        FREQUENCIES[terms["frequency"]],
    )
    expected = ql.BondFunctions.convexity(
        quantlib_bond(terms), rate, qdate(terms["settlement"])
    )
    assert math.isclose(result.convexity, expected, rel_tol=1e-10, abs_tol=1e-12)


# --- cases with exact answers and documented refusals ----------------------------


def test_effective_convexity_off_a_flat_curve_is_close_to_analytical() -> None:
    bond = {"settlement": "2026-01-15", "maturity": "2046-01-15", "coupon_rate": 0.05}
    analytical = run(calculation="analytical", yield_to_maturity=0.05, **bond)
    effective = run(
        calculation="effective",
        curve_tenors=[1.0],
        curve_rates=[0.05],
        bump=0.001,
        **bond,
    )
    assert math.isclose(
        effective.effective_convexity, analytical.convexity, rel_tol=1e-4
    )
    assert math.isclose(effective.full_price, analytical.full_price, rel_tol=1e-13)
