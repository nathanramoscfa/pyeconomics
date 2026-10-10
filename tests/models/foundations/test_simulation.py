# tests/models/foundations/test_simulation.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``foundations.simulation``: its invariants.

The draws are kept small (at most a few thousand paths of a few steps), so each
property runs in milliseconds; the golden file checks the large runs.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pyeconomics.core import SEED_MAX, canonical_json, run_model
from pyeconomics.models.foundations import simulation

SEEDS = st.integers(min_value=0, max_value=SEED_MAX)


def gbm(**overrides: st.SearchStrategy[Any]) -> st.SearchStrategy[dict[str, Any]]:
    """GBM inputs anywhere in the declared bounds, with few paths and steps."""
    fields: dict[str, st.SearchStrategy[Any]] = {
        "calculation": st.just("gbm"),
        "initial_value": st.floats(min_value=0.01, max_value=1e6),
        "drift": st.floats(min_value=-1.0, max_value=1.0),
        "volatility": st.floats(min_value=1e-6, max_value=3.0),
        "horizon": st.floats(min_value=1e-6, max_value=30.0),
        "steps": st.integers(min_value=1, max_value=20),
        "paths": st.integers(min_value=4, max_value=200),
        "antithetic": st.booleans(),
        "seed": SEEDS,
    }
    fields.update(overrides)
    return st.fixed_dictionaries(fields)


BOOTSTRAP = st.fixed_dictionaries(
    {
        "calculation": st.just("bootstrap"),
        "sample": st.lists(
            st.floats(min_value=-1e6, max_value=1e6), min_size=2, max_size=30
        ),
        "statistic": st.sampled_from(["mean", "median", "standard_deviation"]),
        "resamples": st.integers(min_value=2, max_value=200),
        "confidence": st.floats(min_value=0.5, max_value=0.999),
        "seed": SEEDS,
    }
)


@pytest.mark.invariant("foundations.simulation", "terminal_values_positive")
@settings(deadline=None)
@given(raw=gbm())
def test_terminal_values_are_positive(raw: dict[str, Any]) -> None:
    out = run_model(simulation, raw).outputs
    assert out.terminal_min > 0
    assert all(q > 0 for q in out.percentile_values)


@pytest.mark.invariant("foundations.simulation", "same_seed_same_result")
@settings(deadline=None)
@given(raw=st.one_of(gbm(), BOOTSTRAP))
def test_the_same_seed_gives_the_same_result(raw: dict[str, Any]) -> None:
    first = run_model(simulation, raw)
    second = run_model(simulation, raw)
    assert canonical_json(first.outputs.model_dump(mode="json")) == canonical_json(
        second.outputs.model_dump(mode="json")
    )


@pytest.mark.invariant("foundations.simulation", "antithetic_reduces_variance")
@settings(deadline=None, max_examples=25)
@given(
    raw=gbm(
        paths=st.integers(min_value=2_000, max_value=4_000),
        steps=st.integers(min_value=1, max_value=4),
        volatility=st.floats(min_value=1e-3, max_value=1.0),
        horizon=st.floats(min_value=1e-3, max_value=1.0),
        antithetic=st.just(False),  # noqa: FBT003 - the plain run; paired below
    )
)
def test_antithetic_variates_do_not_raise_the_standard_error(
    raw: dict[str, Any],
) -> None:
    # With sigma^2 T <= 1 the correlation of a path with its mirror is at most
    # (e^-1 - 1) / (e - 1) = -0.37, so the antithetic variance is at most 0.63
    # of the plain one; the sampling noise of either estimate at 2,000 paths is
    # a few percent.
    plain = run_model(simulation, raw).outputs.standard_error
    paired = run_model(simulation, {**raw, "antithetic": True}).outputs.standard_error
    assert paired <= plain


def test_a_different_seed_gives_different_draws() -> None:
    raw = {"calculation": "bootstrap", "sample": [1.0, 2.0, 5.0, 9.0], "seed": 1}
    one = run_model(simulation, raw).outputs.standard_error
    two = run_model(simulation, {**raw, "seed": 2}).outputs.standard_error
    assert one != two
    assert math.isfinite(one)
