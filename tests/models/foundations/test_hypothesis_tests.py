# tests/models/foundations/test_hypothesis_tests.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``foundations.hypothesis_tests``: its invariants, and SciPy as an oracle.

The oracle is ``scipy.stats.ttest_ind_from_stats``, SciPy's own two-sample t
test from summary statistics, pooled and Welch. It is imported at the top, so a
missing SciPy fails the suite.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
import scipy.stats
from hypothesis import given, settings
from hypothesis import strategies as st
from strategies import inputs

from pyeconomics.core import run_model
from pyeconomics.models.foundations import hypothesis_tests

ANY_TEST = inputs(hypothesis_tests)
ALTERNATIVES = ("two_sided", "less", "greater")


def run(raw: dict[str, Any]) -> Any:  # noqa: ANN401 - the test's outputs
    return run_model(hypothesis_tests, raw).outputs


@pytest.mark.invariant("foundations.hypothesis_tests", "p_value_in_unit_interval")
@settings(deadline=None)  # the first test imports SciPy
@given(raw=ANY_TEST)
def test_every_p_value_is_a_probability(raw: dict[str, Any]) -> None:
    assert 0.0 <= run(dict(raw)).p_value <= 1.0


@pytest.mark.invariant("foundations.hypothesis_tests", "interval_contains_estimate")
@settings(deadline=None)
@given(raw=ANY_TEST)
def test_the_interval_contains_the_estimate(raw: dict[str, Any]) -> None:
    out = run(dict(raw))
    assert out.ci_lower <= out.estimate <= out.ci_upper


@pytest.mark.invariant("foundations.hypothesis_tests", "two_sided_p_is_twice_one_sided")
@settings(deadline=None)
@given(raw=ANY_TEST)
def test_two_sided_is_twice_the_smaller_tail(raw: dict[str, Any]) -> None:
    p = {alt: run({**raw, "alternative": alt}).p_value for alt in ALTERNATIVES}
    expected = min(1.0, 2.0 * min(p["less"], p["greater"]))
    assert math.isclose(p["two_sided"], expected, rel_tol=1e-9, abs_tol=1e-300)


SIZES = st.integers(min_value=2, max_value=5_000)
MEANS = st.floats(min_value=-1e3, max_value=1e3)
SDS = st.floats(min_value=0.01, max_value=100.0)


TWO_SAMPLES = st.fixed_dictionaries(
    {
        "n1": SIZES,
        "n2": SIZES,
        "mean1": MEANS,
        "mean2": MEANS,
        "sd1": SDS,
        "sd2": SDS,
        "equal_variances": st.booleans(),
        "alternative": st.sampled_from(ALTERNATIVES),
    }
)


@pytest.mark.oracle("foundations.hypothesis_tests")
@settings(deadline=None)
@given(stats=TWO_SAMPLES)
def test_two_sample_t_matches_scipy(stats: dict[str, Any]) -> None:
    ours = run({"calculation": "two_sample_t", **stats})
    theirs = scipy.stats.ttest_ind_from_stats(
        stats["mean1"],
        stats["sd1"],
        stats["n1"],
        stats["mean2"],
        stats["sd2"],
        stats["n2"],
        equal_var=stats["equal_variances"],
        alternative=stats["alternative"].replace("_", "-"),
    )
    assert math.isclose(ours.statistic, float(theirs.statistic), rel_tol=1e-9)
    assert math.isclose(
        ours.p_value, float(theirs.pvalue), rel_tol=1e-6, abs_tol=1e-300
    )


@pytest.mark.oracle("foundations.hypothesis_tests")
@settings(deadline=None)
@given(n=SIZES, mean=MEANS, sd=SDS, mu=MEANS)
def test_paired_and_one_sample_t_match_scipy(
    n: int, mean: float, sd: float, mu: float
) -> None:
    # A one-sample t test is a two-sample one against a constant with a huge,
    # noiseless second sample, in the limit; SciPy states it as Welch's test
    # with the second sample's variance at zero.
    theirs = scipy.stats.ttest_ind_from_stats(mean, sd, n, mu, 0.0, 2, equal_var=False)
    one = run(
        {
            "calculation": "one_sample_t",
            "n": n,
            "mean": mean,
            "sd": sd,
            "hypothesized_mean": mu,
        }
    )
    paired = run(
        {
            "calculation": "paired_t",
            "n": n,
            "mean_difference": mean,
            "sd_difference": sd,
            "hypothesized_difference": mu,
        }
    )
    assert math.isclose(one.statistic, float(theirs.statistic), rel_tol=1e-9)
    assert math.isclose(one.p_value, float(theirs.pvalue), rel_tol=1e-6, abs_tol=1e-300)
    assert paired.statistic == one.statistic
    assert paired.p_value == one.p_value


def test_a_one_sided_test_has_one_critical_value() -> None:
    raw = {"calculation": "f_variances", "n1": 10, "sd1": 2.0, "n2": 12, "sd2": 1.0}
    less = run({**raw, "alternative": "less"})
    greater = run({**raw, "alternative": "greater"})
    assert len(less.critical_values) == len(greater.critical_values) == 1
    assert less.critical_values[0] < 1 < greater.critical_values[0]
    assert greater.reject is (greater.statistic > greater.critical_values[0])
