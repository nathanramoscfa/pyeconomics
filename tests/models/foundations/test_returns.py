# tests/models/foundations/test_returns.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``foundations.returns``: its invariants, and the cases it refuses."""

from __future__ import annotations

import math
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import DomainError, run_model
from pyeconomics.models.foundations import returns

RETURNS = st.floats(min_value=-0.999, max_value=100.0)
SMALL_RETURNS = st.floats(min_value=-0.5, max_value=0.5)
RATES = st.floats(min_value=-0.99, max_value=10.0)
INFLATION = st.floats(min_value=-0.5, max_value=10.0)


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(returns, inputs).outputs


def _slack(value: float) -> float:
    return 1e-12 * (1 + abs(value))


@pytest.mark.invariant("foundations.returns", "means_ordering")
@given(series=st.lists(RETURNS, min_size=1, max_size=40))
def test_harmonic_geometric_arithmetic(series: list[float]) -> None:
    means = run(calculation="means", returns=series)
    assert means.harmonic <= means.geometric + _slack(means.geometric)
    assert means.geometric <= means.arithmetic + _slack(means.arithmetic)
    assert min(series) <= means.harmonic
    assert means.arithmetic <= max(series)


@pytest.mark.invariant("foundations.returns", "log_returns_additive")
@given(series=st.lists(SMALL_RETURNS, min_size=1, max_size=6))
def test_log_returns_add_up(series: list[float]) -> None:
    logs = run(calculation="log", returns=series).converted
    whole = math.prod(1 + r for r in series) - 1
    (total,) = run(calculation="log", returns=[whole]).converted
    assert math.isclose(total, math.fsum(logs), rel_tol=1e-12, abs_tol=1e-12)
    back = run(calculation="log", returns=list(logs), direction="log_to_simple")
    for simple, again in zip(series, back.converted, strict=True):
        assert math.isclose(simple, again, rel_tol=1e-12, abs_tol=1e-15)


@pytest.mark.invariant("foundations.returns", "fisher_identity")
@given(nominal=RATES, inflation=INFLATION)
def test_the_fisher_relation_holds(nominal: float, inflation: float) -> None:
    real = run(calculation="real", nominal=nominal, inflation=inflation).real
    assert math.isclose((1 + real) * (1 + inflation), 1 + nominal, rel_tol=1e-12)


def test_annualizing_a_total_loss_is_a_total_loss() -> None:
    annual = run(calculation="annualized", period_return=-1.0, periods_per_year=12)
    assert annual.annualized_return == -1.0


def test_a_multi_period_return_annualizes_by_its_span() -> None:
    annual = run(
        calculation="annualized", period_return=0.21, periods=2, periods_per_year=1
    )
    assert math.isclose(annual.annualized_return, 0.1, rel_tol=1e-12)


@pytest.mark.parametrize(
    "inputs",
    [
        {"calculation": "annualized", "period_return": 1.0, "periods_per_year": 12},
        {"calculation": "log", "returns": [0.1, -1.0]},
        {"calculation": "log", "returns": [5.0], "direction": "log_to_simple"},
        {"calculation": "holding_period", "beginning_value": 1e-6, "ending_value": 1},
    ],
    ids=[
        "annualized_above_bounds",
        "log_of_a_total_loss",
        "simple_above_bounds",
        "holding_period_above_bounds",
    ],
)
def test_inputs_with_no_answer_raise_a_domain_error(inputs: dict[str, Any]) -> None:
    with pytest.raises(DomainError):
        run_model(returns, inputs)


# --- regressions from the Step 6 review --------------------------------------


def test_a_return_at_its_upper_bound_round_trips() -> None:
    annual = run(calculation="annualized", period_return=100.0, periods_per_year=1)
    assert annual.annualized_return == 100.0
    back = run(
        calculation="log", returns=[math.log1p(100.0)], direction="log_to_simple"
    )
    assert back.converted == (100.0,)


def test_a_zero_return_annualizes_to_zero_at_any_exponent() -> None:
    annual = run(
        calculation="annualized",
        period_return=0.0,
        periods=2.2250738585072014e-308,
        periods_per_year=100_000,
    )
    assert annual.annualized_return == 0.0
