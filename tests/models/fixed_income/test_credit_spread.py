# tests/models/fixed_income/test_credit_spread.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``fixed_income.credit_spread``: its invariants and exact cases.

No independent library computes these closed forms, so there is no oracle test;
the golden file holds them to Hull's worked example and to identities.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import InputError, run_model
from pyeconomics.models.fixed_income import credit_spread

PROBABILITIES = st.floats(min_value=0.0, max_value=1.0)
RECOVERIES = st.floats(min_value=0.0, max_value=0.9)


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(credit_spread, inputs).outputs


@pytest.mark.invariant("fixed_income.credit_spread", "spread_hazard_round_trip")
@given(spread=st.floats(min_value=0.0, max_value=1.0), recovery=RECOVERIES)
def test_the_spread_of_the_implied_hazard_is_the_spread(
    spread: float, recovery: float
) -> None:
    hazard = run(
        calculation="hazard_from_spread", spread=spread, recovery_rate=recovery
    ).hazard_rate
    back = run(
        calculation="spread_from_hazard", hazard_rate=hazard, recovery_rate=recovery
    ).spread
    assert math.isclose(back, spread, rel_tol=1e-14, abs_tol=1e-15)


@pytest.mark.invariant("fixed_income.credit_spread", "survival_decreases_with_horizon")
@given(
    hazard=st.floats(min_value=0.0, max_value=10.0),
    near=st.floats(min_value=0.0, max_value=100.0),
    far=st.floats(min_value=0.0, max_value=100.0),
)
def test_survival_does_not_rise_with_the_horizon(
    hazard: float, near: float, far: float
) -> None:
    near, far = sorted((near, far))
    first = run(calculation="survival", hazard_rate=hazard, horizon=near)
    later = run(calculation="survival", hazard_rate=hazard, horizon=far)
    assert later.survival_probability <= first.survival_probability
    assert later.default_probability >= first.default_probability
    assert math.isclose(
        first.survival_probability + first.default_probability, 1.0, rel_tol=1e-15
    )


@pytest.mark.invariant("fixed_income.credit_spread", "expected_loss_within_exposure")
@given(
    pd=PROBABILITIES,
    lgd=PROBABILITIES,
    exposure=st.floats(min_value=0.0, max_value=1e12),
)
def test_the_expected_loss_is_within_the_exposure(
    pd: float, lgd: float, exposure: float
) -> None:
    result = run(
        calculation="expected_loss",
        probability_of_default=pd,
        loss_given_default=lgd,
        exposure=exposure,
    )
    assert 0.0 <= result.expected_loss <= exposure
    assert 0.0 <= result.loss_rate <= 1.0


def test_the_spread_return_adds_up() -> None:
    result = run(
        calculation="spread_return",
        spread=0.02,
        holding_period=0.5,
        spread_duration=4.0,
        spread_change=-0.005,
        probability_of_default=0.0,
        loss_given_default=0.6,
    )
    assert math.isclose(result.carry, 0.01)
    assert math.isclose(result.spread_change_return, 0.02)
    assert result.expected_loss == 0.0
    assert math.isclose(result.spread_return, 0.03)


def test_a_recovery_of_all_par_is_refused() -> None:
    with pytest.raises(InputError, match="recovery_rate"):
        run(calculation="hazard_from_spread", spread=0.02, recovery_rate=1.0)
