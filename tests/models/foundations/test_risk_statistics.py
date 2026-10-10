# tests/models/foundations/test_risk_statistics.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``foundations.risk_statistics``: its invariants, and SciPy as an oracle.

The oracle is ``scipy.stats.skew`` and ``scipy.stats.kurtosis`` with
``bias=False``, the G1 and G2 estimators, and NumPy's ``std`` with ``ddof=1``.
Both are imported at the top, so a missing library fails the suite.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
import scipy.stats
from hypothesis import assume, given
from hypothesis import strategies as st

from pyeconomics.core import DomainError, run_model
from pyeconomics.models.foundations import risk_statistics

SMALL = st.floats(min_value=-0.09, max_value=0.09)
MODERATE = st.floats(min_value=-0.4, max_value=0.4)
SERIES = st.lists(MODERATE, min_size=4, max_size=60)


def run(**inputs: Any) -> Any:  # noqa: ANN401 - the calculation's outputs
    return run_model(risk_statistics, inputs).outputs


def volatility(series: list[float]) -> float:
    out = run(calculation="volatility", returns=series, periods_per_year=1)
    return float(out.volatility)


@pytest.mark.invariant("foundations.risk_statistics", "volatility_scale_equivariant")
@given(
    series=st.lists(SMALL, min_size=2, max_size=60),
    scale=st.floats(min_value=-10.0, max_value=10.0),
)
def test_scaling_returns_scales_the_volatility(
    series: list[float], scale: float
) -> None:
    scaled = volatility([scale * r for r in series])
    assert math.isclose(
        scaled, abs(scale) * volatility(series), rel_tol=1e-9, abs_tol=1e-15
    )


@pytest.mark.invariant("foundations.risk_statistics", "volatility_shift_invariant")
@given(
    series=st.lists(MODERATE, min_size=2, max_size=60),
    shift=st.floats(min_value=-0.5, max_value=0.5),
)
def test_shifting_returns_keeps_the_volatility(
    series: list[float], shift: float
) -> None:
    shifted = volatility([r + shift for r in series])
    assert math.isclose(shifted, volatility(series), rel_tol=1e-9, abs_tol=1e-14)


@pytest.mark.invariant("foundations.risk_statistics", "drawdown_between_zero_and_one")
@given(
    values=st.lists(st.floats(min_value=1e-3, max_value=1e9), min_size=1, max_size=60)
)
def test_a_drawdown_is_a_fraction_with_its_peak_first(values: list[float]) -> None:
    found = run(calculation="drawdown", values=values)
    assert 0.0 <= found.max_drawdown <= 1.0
    assert found.peak_index <= found.trough_index < len(values)
    if found.max_drawdown > 0:
        peak, trough = values[found.peak_index], values[found.trough_index]
        assert math.isclose(found.max_drawdown, 1 - trough / peak, rel_tol=1e-12)
        assert peak == max(values[: found.trough_index + 1])


@pytest.mark.oracle("foundations.risk_statistics")
@given(series=SERIES)
def test_moments_match_scipy(series: list[float]) -> None:
    data = np.asarray(series)
    assume(float(np.ptp(data)) > 1e-3)
    shape = run(calculation="moments", returns=series)
    assert math.isclose(
        shape.skewness,
        float(scipy.stats.skew(data, bias=False)),
        rel_tol=1e-9,
        abs_tol=1e-9,
    )
    assert math.isclose(
        shape.excess_kurtosis,
        float(scipy.stats.kurtosis(data, bias=False)),
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


@pytest.mark.oracle("foundations.risk_statistics")
@given(series=st.lists(MODERATE, min_size=2, max_size=60))
def test_volatility_matches_numpy(series: list[float]) -> None:
    out = run(calculation="volatility", returns=series, periods_per_year=252)
    expected = float(np.std(np.asarray(series), ddof=1))
    assert math.isclose(out.volatility, expected, rel_tol=1e-9, abs_tol=1e-15)
    assert math.isclose(
        out.annualized_volatility,
        expected * math.sqrt(252),
        rel_tol=1e-9,
        abs_tol=1e-14,
    )


def test_moments_of_a_constant_series_are_undefined() -> None:
    with pytest.raises(DomainError):
        run_model(risk_statistics, {"calculation": "moments", "returns": [0.1] * 5})
