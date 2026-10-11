# tests/models/fixed_income/test_duration.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``fixed_income.duration``: its invariants, QuantLib as an oracle, refusals.

The oracle is QuantLib's ``BondFunctions.duration`` (Macaulay and modified) on
the same bond, at the same yield compounded at the coupon frequency.
"""

from __future__ import annotations

import datetime as dt
import math
from itertools import pairwise
from typing import Any

import pytest
import QuantLib as ql  # type: ignore[import-untyped]  # noqa: N813 - oracle docs use ql
from fixed_income_draws import DAY_COUNTS, FREQUENCIES, bonds, qdate, quantlib_bond
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from pyeconomics.core import DomainError, InputError, run_model
from pyeconomics.models.fixed_income import duration

YIELDS = st.floats(min_value=-0.02, max_value=0.25)
PERIODS = {"annual": 1, "semiannual": 2, "quarterly": 4, "monthly": 12}


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(duration, inputs).outputs


@pytest.mark.invariant("fixed_income.duration", "zero_coupon_macaulay_equals_maturity")
@given(
    terms=bonds(irregular=False, coupon=st.just(0.0)),
    periods=st.integers(min_value=1, max_value=600),
    y=YIELDS,
)
def test_a_zero_coupon_bonds_duration_is_its_maturity(
    terms: dict[str, Any], periods: int, y: float
) -> None:
    f = PERIODS[terms["frequency"]]
    maturity = terms["maturity"]
    year, month = divmod(
        maturity.year * 12 + maturity.month - 1 - periods * 12 // f, 12
    )
    assume(year >= 1902 and periods * 12 // f <= 1200)
    on_date = {**terms, "settlement": dt.date(year, month + 1, maturity.day)}
    result = run(calculation="macaulay_modified", yield_to_maturity=y, **on_date)
    assert math.isclose(result.macaulay_duration, periods / f, rel_tol=1e-14)
    between = run(calculation="macaulay_modified", yield_to_maturity=y, **terms)
    # Between coupon dates, the one payment is the whole time to maturity away.
    assert math.isclose(
        between.full_price,
        100 * (1 + y / f) ** -(between.macaulay_duration * f),
        rel_tol=1e-10,
    )


@pytest.mark.invariant(
    "fixed_income.duration", "modified_equals_macaulay_over_periodic_factor"
)
@given(terms=bonds(), y=YIELDS)
def test_modified_duration_is_macaulay_over_one_plus_y_over_f(
    terms: dict[str, Any], y: float
) -> None:
    result = run(calculation="macaulay_modified", yield_to_maturity=y, **terms)
    f = PERIODS[terms["frequency"]]
    assert math.isclose(
        result.modified_duration, result.macaulay_duration / (1 + y / f), rel_tol=1e-14
    )


@pytest.mark.invariant("fixed_income.duration", "key_rates_sum_to_effective")
@settings(deadline=None)
@given(
    terms=bonds(max_years=30),
    data=st.data(),
    size=st.integers(min_value=1, max_value=6),
)
def test_key_rate_durations_sum_to_the_effective_duration(
    terms: dict[str, Any], data: st.DataObject, size: int
) -> None:
    tenors = sorted(
        data.draw(
            st.lists(
                st.floats(min_value=0.25, max_value=40.0),
                min_size=size,
                max_size=size,
                unique=True,
            )
        )
    )
    assume(all(b - a > 1e-3 for a, b in pairwise(tenors)))
    rates = data.draw(
        st.lists(st.floats(min_value=0.0, max_value=0.12), min_size=size, max_size=size)
    )
    keys = sorted(
        data.draw(
            st.lists(
                st.sampled_from([0.5, 2.0, 5.0, 10.0, 30.0]), min_size=1, unique=True
            )
        )
    )
    result = run(
        calculation="key_rate",
        curve_tenors=tenors,
        curve_rates=rates,
        key_tenors=keys,
        **terms,
    )
    # The central difference's third-order term differs between the two sums by
    # at most about bump^2 x T^2 of the duration, for T up to 30 years.
    total = math.fsum(result.key_rate_durations)
    assert math.isclose(total, result.effective_duration, rel_tol=1e-4, abs_tol=1e-9)


@pytest.mark.invariant("fixed_income.duration", "duration_falls_as_coupon_rises")
@given(
    terms=bonds(),
    y=YIELDS,
    low=st.floats(min_value=0.0, max_value=0.3),
    high=st.floats(min_value=0.0, max_value=0.3),
)
def test_a_higher_coupon_gives_a_duration_no_longer(
    terms: dict[str, Any], y: float, low: float, high: float
) -> None:
    low, high = sorted((low, high))
    at_low = run(
        calculation="macaulay_modified",
        yield_to_maturity=y,
        **{**terms, "coupon_rate": low},
    )
    at_high = run(
        calculation="macaulay_modified",
        yield_to_maturity=y,
        **{**terms, "coupon_rate": high},
    )
    assert at_high.macaulay_duration <= at_low.macaulay_duration * (1 + 1e-12)


@pytest.mark.invariant("fixed_income.duration", "dv01_positive")
@given(terms=bonds(), y=YIELDS, face=st.floats(min_value=1.0, max_value=1e9))
def test_dv01_is_positive(terms: dict[str, Any], y: float, face: float) -> None:
    result = run(calculation="dv01", yield_to_maturity=y, face_value=face, **terms)
    assert result.dv01 > 0
    assert math.isclose(
        result.dv01, result.modified_duration * result.full_price * 1e-4, rel_tol=1e-14
    )


# --- QuantLib as an oracle -------------------------------------------------------


@pytest.mark.oracle("fixed_income.duration")
@given(terms=bonds(), y=st.floats(min_value=-0.01, max_value=0.2))
def test_macaulay_and_modified_agree_with_quantlib(
    terms: dict[str, Any], y: float
) -> None:
    result = run(calculation="macaulay_modified", yield_to_maturity=y, **terms)
    rate = ql.InterestRate(
        y,
        DAY_COUNTS[terms["day_count"]],
        ql.Compounded,
        FREQUENCIES[terms["frequency"]],
    )
    bond = quantlib_bond(terms)
    settlement = qdate(terms["settlement"])
    macaulay = ql.BondFunctions.duration(bond, rate, ql.Duration.Macaulay, settlement)
    modified = ql.BondFunctions.duration(bond, rate, ql.Duration.Modified, settlement)
    assert math.isclose(
        result.macaulay_duration, macaulay, rel_tol=1e-11, abs_tol=1e-12
    )
    assert math.isclose(
        result.modified_duration, modified, rel_tol=1e-11, abs_tol=1e-12
    )


# --- cases with exact answers and documented refusals ----------------------------


def test_effective_duration_off_a_flat_curve_is_close_to_modified() -> None:
    bond = {"settlement": "2026-01-15", "maturity": "2046-01-15", "coupon_rate": 0.05}
    modified = run(calculation="macaulay_modified", yield_to_maturity=0.05, **bond)
    effective = run(
        calculation="effective", curve_tenors=[1.0], curve_rates=[0.05], **bond
    )
    assert math.isclose(effective.full_price, modified.full_price, rel_tol=1e-13)
    assert math.isclose(
        effective.effective_duration, modified.modified_duration, rel_tol=1e-6
    )
    assert effective.price_down > effective.full_price > effective.price_up


def test_a_key_with_no_cash_flow_nearby_has_no_duration() -> None:
    result = run(
        calculation="key_rate",
        settlement="2026-01-15",
        maturity="2028-01-15",
        coupon_rate=0.05,
        curve_tenors=[1.0, 2.0],
        curve_rates=[0.04, 0.045],
        key_tenors=[1.0, 2.0, 30.0],
    )
    assert result.key_rate_durations[-1] == 0.0


def test_an_overflowing_price_off_a_curve_is_a_domain_error() -> None:
    with pytest.raises(DomainError, match="price down"):
        run(
            calculation="effective",
            settlement="2026-01-15",
            maturity="2125-12-15",
            frequency="annual",
            coupon_rate=1.0,
            face_value=1e9,
            redemption=200.0,
            curve_tenors=[1.0],
            curve_rates=[-0.1],
            bump=0.01,
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"curve_rates": [0.04]}, "one spot rate per tenor"),
        ({"curve_tenors": [2.0, 1.0]}, "strictly increasing"),
        ({"key_tenors": [5.0, 5.0]}, "key tenors"),
    ],
)
def test_inconsistent_curves_are_refused(change: dict[str, Any], message: str) -> None:
    inputs = {
        "calculation": "key_rate",
        "settlement": "2026-01-15",
        "maturity": "2036-01-15",
        "coupon_rate": 0.05,
        "curve_tenors": [1.0, 2.0],
        "curve_rates": [0.04, 0.045],
        "key_tenors": [2.0, 5.0],
        **change,
    }
    with pytest.raises(InputError, match=message):
        run(**inputs)
