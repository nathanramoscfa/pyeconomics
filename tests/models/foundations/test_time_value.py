# tests/models/foundations/test_time_value.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``foundations.time_value``: its invariants, and the cases it refuses.

Runs go through ``run_model``, which collects the model's warnings, so an IRR
left undefined reports why instead of raising under ``filterwarnings = error``.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from pyeconomics.core import DomainError, InputError, run_model
from pyeconomics.models.foundations import time_value

RATES = st.floats(min_value=-0.5, max_value=0.5, allow_nan=False)
POSITIVE_RATES = st.floats(min_value=1e-4, max_value=0.5)
PERIODS = st.floats(min_value=0.0, max_value=200.0)
WHOLE_PERIODS = st.integers(min_value=1, max_value=360)
AMOUNTS = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(time_value, inputs).outputs


def conventional_flows() -> st.SearchStrategy[list[float]]:
    """An outlay at time 0, then inflows that are not all zero."""
    return (
        st.tuples(
            st.floats(min_value=1.0, max_value=1e6),
            st.lists(st.floats(min_value=0.0, max_value=1e6), min_size=1, max_size=30),
        )
        .filter(lambda t: any(t[1]))
        .map(lambda t: [-t[0], *t[1]])
    )


@pytest.mark.invariant("foundations.time_value", "pv_fv_inverse")
@given(rate=RATES, periods=PERIODS, amount=AMOUNTS)
def test_compounding_a_present_value_returns_the_sum(
    rate: float, periods: float, amount: float
) -> None:
    assume(abs(periods * math.log1p(rate)) < 13)  # keeps both values in bounds
    pv = run(
        calculation="present_value", rate=rate, periods=periods, future_value=amount
    ).present_value
    fv = run(
        calculation="future_value", rate=rate, periods=periods, present_value=pv
    ).future_value
    assert math.isclose(fv, amount, rel_tol=1e-12, abs_tol=1e-9)


@pytest.mark.invariant("foundations.time_value", "npv_zero_at_irr")
@settings(deadline=None)  # the first root search imports SciPy
@given(flows=conventional_flows())
def test_the_npv_at_the_irr_is_zero(flows: list[float]) -> None:
    irr = run(calculation="irr", cash_flows=flows).irr
    assume(irr is not None and irr <= 1.0)  # npv takes rates up to 100%
    npv = run(calculation="npv", rate=irr, cash_flows=flows).npv
    scale = math.fsum(abs(f) for f in flows) * len(flows)
    assert abs(npv) <= 1e-9 * scale


@pytest.mark.invariant("foundations.time_value", "npv_decreasing_in_rate")
@given(flows=conventional_flows(), low=RATES, high=RATES)
def test_the_npv_falls_as_the_rate_rises(
    flows: list[float], low: float, high: float
) -> None:
    low, high = sorted((low, high))
    assume(high - low > 1e-9)
    at_low = run(calculation="npv", rate=low, cash_flows=flows).npv
    at_high = run(calculation="npv", rate=high, cash_flows=flows).npv
    assert at_high <= at_low + 1e-9 * max(1.0, abs(at_low))


@pytest.mark.invariant("foundations.time_value", "annuity_due_ratio")
@given(rate=RATES, periods=PERIODS, payment=AMOUNTS, growth=RATES)
def test_an_annuity_due_is_worth_one_plus_r_times_more(
    rate: float, periods: float, payment: float, growth: float
) -> None:
    assume(abs(periods * math.log1p(rate)) < 13)
    assume(abs(periods * math.log1p(growth)) < 13)
    common = {"rate": rate, "periods": periods, "payment": payment, "growth": growth}
    arrears = run(calculation="present_value", **common).present_value
    due = run(calculation="present_value", due=True, **common).present_value
    assert math.isclose(due, (1 + rate) * arrears, rel_tol=1e-12, abs_tol=1e-9)
    later = run(calculation="future_value", **common).future_value
    later_due = run(calculation="future_value", due=True, **common).future_value
    assert math.isclose(later_due, (1 + rate) * later, rel_tol=1e-12, abs_tol=1e-9)


@pytest.mark.invariant("foundations.time_value", "amortization_ends_at_zero")
@given(
    principal=st.floats(min_value=1.0, max_value=1e9),
    rate=st.floats(min_value=-0.99, max_value=1.0),
    periods=WHOLE_PERIODS,
)
def test_a_schedule_repays_the_principal(
    principal: float, rate: float, periods: int
) -> None:
    schedule = run(
        calculation="amortization", principal=principal, rate=rate, periods=periods
    )
    assert schedule.balance[-1] == 0.0
    assert len(schedule.payment) == periods
    assert math.isclose(math.fsum(schedule.principal), principal, rel_tol=1e-9)
    assert all(b >= -1e-9 * principal for b in schedule.balance)


# --- cases with exact answers and documented refusals ----------------------------


def test_the_solve_fills_in_the_omitted_term() -> None:
    known = {"rate": 0.01, "periods": 24.0, "present_value": 1000.0}
    payment = run(calculation="solve", future_value=0.0, **known).payment
    back = run(
        calculation="solve",
        rate=0.01,
        payment=payment,
        present_value=1000.0,
        future_value=0.0,
    )
    assert back.solved_for == "periods"
    assert math.isclose(back.periods, 24.0, rel_tol=1e-12)
    at_zero = run(
        calculation="solve",
        rate=0.0,
        payment=-100.0,
        present_value=1000.0,
        future_value=0.0,
    )
    assert math.isclose(at_zero.periods, 10.0)


def test_a_growing_annuity_equals_its_cash_flows() -> None:
    rate, growth = 0.07, 0.03
    flows = [0.0] + [100 * (1 + growth) ** (t - 1) for t in range(1, 11)]
    npv = run(calculation="npv", rate=rate, cash_flows=flows).npv
    pv = run(
        calculation="present_value",
        rate=rate,
        periods=10,
        payment=100,
        growth=growth,
    ).present_value
    fv = run(
        calculation="future_value",
        rate=rate,
        periods=10,
        payment=100,
        growth=growth,
    ).future_value
    assert math.isclose(pv, npv, rel_tol=1e-12)
    assert math.isclose(fv, npv * (1 + rate) ** 10, rel_tol=1e-12)
    same = run(
        calculation="present_value", rate=0.05, periods=10, payment=1, growth=0.05
    ).present_value
    assert math.isclose(same, 10 / 1.05, rel_tol=1e-12)


def test_an_irr_with_several_roots_warns() -> None:
    result = run_model(
        time_value, {"calculation": "irr", "cash_flows": [-100, 230, -132]}
    )
    assert math.isclose(result.outputs.irr, 0.1, rel_tol=1e-9)
    assert [w.code for w in result.warnings] == ["several_roots"]


def test_an_irr_outside_the_bracket_is_undefined() -> None:
    result = run_model(time_value, {"calculation": "irr", "cash_flows": [-1, 100]})
    assert result.outputs.irr is None
    assert [w.code for w in result.warnings] == ["no_root_in_range"]


def test_an_xirr_with_one_sign_is_undefined() -> None:
    result = run_model(
        time_value,
        {
            "calculation": "xirr",
            "cash_flows": [10, 20],
            "dates": ["2020-01-01", "2021-01-01"],
        },
    )
    assert result.outputs.xirr is None
    assert [w.code for w in result.warnings] == ["no_sign_change"]


@pytest.mark.parametrize(
    "inputs",
    [
        {"calculation": "present_value", "rate": 0.03, "payment": 1, "growth": 0.05},
        {"calculation": "present_value", "rate": 0.05, "payment": 1, "future_value": 9},
        {
            "calculation": "future_value",
            "rate": 1.0,
            "periods": 1200,
            "present_value": 1,
        },
        {
            "calculation": "npv",
            "rate": -0.99,
            "cash_flows": [0, 0, 0, 0, 0, 0, 0, 0, 1e12],
        },
        {
            "calculation": "solve",
            "periods": 0,
            "present_value": 1,
            "payment": 1,
            "future_value": 1,
        },
        {
            "calculation": "solve",
            "periods": 10,
            "present_value": 1,
            "payment": 1,
            "future_value": 1,
        },
        {
            "calculation": "solve",
            "rate": 0,
            "present_value": 1,
            "payment": 0,
            "future_value": 1,
        },
        {
            "calculation": "solve",
            "rate": 0.1,
            "present_value": 1,
            "payment": 0,
            "future_value": 1,
        },
        {
            "calculation": "solve",
            "rate": 0.1,
            "present_value": -1,
            "payment": 0.1,
            "future_value": 0,
        },
        {
            "calculation": "solve",
            "rate": 0.1,
            "periods": 0,
            "present_value": 1,
            "future_value": 1,
        },
        {
            "calculation": "solve",
            "rate": 0,
            "periods": 1200,
            "present_value": 1,
            "payment": 1e12,
        },
    ],
    ids=[
        "perpetuity_rate_below_growth",
        "perpetuity_with_a_final_sum",
        "future_value_out_of_bounds",
        "npv_out_of_bounds",
        "rate_over_zero_periods",
        "no_rate_balances",
        "periods_with_no_rate_or_payment",
        "periods_with_no_payment_and_wrong_signs",
        "periods_where_the_payment_only_covers_interest",
        "payment_over_zero_periods",
        "future_value_out_of_bounds_in_solve",
    ],
)
def test_inputs_with_no_answer_raise_a_domain_error(inputs: dict[str, Any]) -> None:
    with pytest.raises(DomainError):
        run_model(time_value, inputs)


@pytest.mark.parametrize(
    "inputs",
    [
        {"calculation": "solve", "rate": 0.1, "periods": 2, "present_value": 1},
        {
            "calculation": "solve",
            "rate": 0.1,
            "periods": 2,
            "present_value": 1,
            "payment": 1,
            "future_value": 1,
        },
        {
            "calculation": "xnpv",
            "rate": 0.1,
            "cash_flows": [1, 2],
            "dates": ["2020-01-01"],
        },
    ],
    ids=["two_omitted", "none_omitted", "a_date_missing"],
)
def test_inputs_that_break_a_rule_between_fields_are_refused(
    inputs: dict[str, Any],
) -> None:
    with pytest.raises(InputError):
        run_model(time_value, inputs)


def test_a_negative_rate_loan_still_amortizes() -> None:
    schedule = run(calculation="amortization", principal=1000, rate=-0.5, periods=1200)
    assert schedule.balance[-1] == 0.0
    assert schedule.balance[0] == pytest.approx(500.0, rel=1e-12)
    assert schedule.level_payment == pytest.approx(0.0, abs=1e-300)


# --- regressions from the Step 6 review --------------------------------------


def test_the_largest_loan_stays_within_its_bounds() -> None:
    schedule = run(calculation="amortization", principal=1e12, rate=1.0, periods=1200)
    assert math.isclose(
        schedule.total_interest, 1200 * 1e12 * 2 / 2 - 1e12, rel_tol=1e-9
    )


@pytest.mark.parametrize("rate", [1e-8, 1e-14, 1e-16, 1e-300, -1e-12])
def test_periods_at_a_tiny_rate_keep_their_digits(rate: float) -> None:
    found = run(
        calculation="solve",
        rate=rate,
        payment=-100.0,
        present_value=1000.0,
        future_value=0.0,
    )
    assert math.isclose(found.periods, 10.0, rel_tol=1e-6)


def test_a_payment_behind_an_infinite_annuity_factor_is_finite() -> None:
    found = run(
        calculation="solve",
        periods=1200,
        rate=-0.99,
        present_value=1e12,
        future_value=1.0,
    )
    assert math.isclose(found.payment, -0.99, rel_tol=1e-9)


def test_a_future_value_with_offsetting_infinite_terms_is_finite() -> None:
    # PV + PMT / r = 0: FV = PMT / r however long it compounds.
    found = run(
        calculation="solve",
        periods=1200,
        rate=1.0,
        present_value=-100.0,
        payment=100.0,
    )
    assert found.future_value == pytest.approx(100.0)
