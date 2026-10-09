# tests/unit/core/test_compounding.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Frequencies, compounding and rate conversions against closed forms.

The expected values were computed independently with 40-digit ``decimal``
arithmetic from the closed forms in the module docstring.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from pyeconomics.core import (
    Compounding,
    DomainError,
    Frequency,
    InputError,
    accumulation_factor,
    convert_rate,
    discount_factor,
    effective_annual_rate,
    implied_rate,
)


def close(expected: float) -> object:
    """Agree with a closed form to 13 significant digits."""
    return pytest.approx(expected, rel=1e-13, abs=1e-15)


def test_periods_per_year() -> None:
    assert {f: f.periods_per_year for f in Frequency} == {
        Frequency.ANNUAL: 1,
        Frequency.SEMIANNUAL: 2,
        Frequency.QUARTERLY: 4,
        Frequency.MONTHLY: 12,
        Frequency.WEEKLY: 52,
        Frequency.DAILY: 365,
    }


@pytest.mark.parametrize("frequency", list(Frequency))
def test_pandas_aliases_are_valid_pandas_3_offsets(frequency: Frequency) -> None:
    index = pd.date_range("2026-01-01", periods=3, freq=frequency.pandas_alias)
    assert len(index) == 3


@pytest.mark.parametrize("removed", ["M", "Q", "Y"])
def test_pandas_3_rejects_the_old_aliases(removed: str) -> None:
    with pytest.raises(ValueError, match=r"no longer supported|Invalid frequency"):
        pd.date_range("2026-01-01", periods=3, freq=removed)


def test_enum_values_are_stable_strings() -> None:
    assert [c.value for c in Compounding] == ["simple", "periodic", "continuous"]
    assert Frequency("semiannual") is Frequency.SEMIANNUAL


@pytest.mark.parametrize(
    ("rate", "years", "compounding", "frequency", "factor"),
    [
        (0.05, 2.0, Compounding.SIMPLE, None, 1.1),
        (0.05, 2.0, Compounding.PERIODIC, Frequency.ANNUAL, 1.1025),
        (0.04, 5.0, Compounding.PERIODIC, Frequency.SEMIANNUAL, 1.218994419994757),
        (0.05, 10.0, Compounding.CONTINUOUS, None, 1.648721270700128),
        (0.0, 30.0, Compounding.CONTINUOUS, None, 1.0),
        (-0.01, 3.0, Compounding.PERIODIC, Frequency.ANNUAL, 0.970299),
        (0.05, 0.0, Compounding.PERIODIC, Frequency.MONTHLY, 1.0),
    ],
)
def test_accumulation_and_discount_factors(
    rate: float,
    years: float,
    compounding: Compounding,
    frequency: Frequency | None,
    factor: float,
) -> None:
    assert accumulation_factor(rate, years, compounding, frequency) == close(factor)
    assert discount_factor(rate, years, compounding, frequency) == close(1 / factor)


def test_discount_factor_closed_forms() -> None:
    # 1 / 1.02**10 and exp(-0.5), from 40-digit decimals.
    assert discount_factor(
        0.04, 5, Compounding.PERIODIC, Frequency.SEMIANNUAL
    ) == close(0.8203482998751552769979725)
    assert discount_factor(0.05, 10, Compounding.CONTINUOUS) == close(
        0.6065306597126334236037995
    )


@pytest.mark.parametrize(
    ("rate", "compounding", "frequency", "ear"),
    [
        (0.12, Compounding.PERIODIC, Frequency.MONTHLY, 0.1268250301319697206612),
        (0.06, Compounding.PERIODIC, Frequency.MONTHLY, 0.0616778118644995687897),
        (0.05, Compounding.CONTINUOUS, None, 0.0512710963760240396975),
        (0.05, Compounding.SIMPLE, None, 0.05),
        (0.05, Compounding.PERIODIC, Frequency.ANNUAL, 0.05),
    ],
)
def test_effective_annual_rate(
    rate: float, compounding: Compounding, frequency: Frequency | None, ear: float
) -> None:
    assert effective_annual_rate(rate, compounding, frequency) == close(ear)


def test_convert_rate_closed_forms() -> None:
    # 2 * (exp(0.025) - 1) and ln(1.05).
    assert convert_rate(
        0.05,
        Compounding.CONTINUOUS,
        Compounding.PERIODIC,
        to_frequency=Frequency.SEMIANNUAL,
    ) == close(0.0506302410488576813560421)
    assert convert_rate(
        0.05,
        Compounding.PERIODIC,
        Compounding.CONTINUOUS,
        from_frequency=Frequency.ANNUAL,
    ) == close(0.0487901641694320030654)


def test_simple_conversion_depends_on_the_horizon() -> None:
    # 1.05**2 = 1.1025 over two years is 5.125% simple interest per year.
    assert convert_rate(
        0.05,
        Compounding.PERIODIC,
        Compounding.SIMPLE,
        from_frequency=Frequency.ANNUAL,
        years=2.0,
    ) == close(0.05125)


@pytest.mark.parametrize(
    ("factor", "years", "compounding", "frequency", "rate"),
    [
        (1.1, 2.0, Compounding.SIMPLE, None, 0.05),
        (1.1025, 2.0, Compounding.PERIODIC, Frequency.ANNUAL, 0.05),
        (math.e, 1.0, Compounding.CONTINUOUS, None, 1.0),
    ],
)
def test_implied_rate_inverts_the_factor(
    factor: float,
    years: float,
    compounding: Compounding,
    frequency: Frequency | None,
    rate: float,
) -> None:
    assert implied_rate(factor, years, compounding, frequency) == close(rate)


def test_periodic_compounding_needs_a_frequency() -> None:
    with pytest.raises(InputError, match="needs a frequency"):
        accumulation_factor(0.05, 1.0, Compounding.PERIODIC)


@pytest.mark.parametrize("compounding", [Compounding.SIMPLE, Compounding.CONTINUOUS])
def test_only_periodic_compounding_takes_a_frequency(compounding: Compounding) -> None:
    with pytest.raises(InputError, match="takes no frequency"):
        accumulation_factor(0.05, 1.0, compounding, Frequency.ANNUAL)


@pytest.mark.parametrize(
    ("rate", "years", "message"),
    [
        (math.nan, 1.0, "finite"),
        (0.05, math.inf, "finite"),
        (0.05, -1.0, "negative"),
    ],
)
def test_factor_inputs_are_checked(rate: float, years: float, message: str) -> None:
    with pytest.raises(InputError, match=message):
        accumulation_factor(rate, years, Compounding.CONTINUOUS)


def test_a_periodic_rate_below_minus_100_percent_is_undefined() -> None:
    with pytest.raises(DomainError, match="below -100%"):
        accumulation_factor(-2.5, 1.0, Compounding.PERIODIC, Frequency.SEMIANNUAL)


def test_a_simple_factor_that_is_not_positive_is_undefined() -> None:
    with pytest.raises(DomainError, match="not positive"):
        accumulation_factor(-0.5, 2.0, Compounding.SIMPLE)


def test_a_continuous_factor_that_underflows_is_undefined() -> None:
    with pytest.raises(DomainError, match="not positive"):
        accumulation_factor(-10.0, 200.0, Compounding.CONTINUOUS)


@pytest.mark.parametrize(
    ("factor", "years", "message"),
    [
        (0.0, 1.0, "positive"),
        (-1.0, 1.0, "positive"),
        (math.inf, 1.0, "finite"),
        (1.1, 0.0, "positive"),
        (1.1, math.nan, "finite"),
    ],
)
def test_implied_rate_inputs_are_checked(
    factor: float, years: float, message: str
) -> None:
    with pytest.raises(InputError, match=message):
        implied_rate(factor, years, Compounding.SIMPLE)
