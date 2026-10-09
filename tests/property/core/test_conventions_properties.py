# tests/property/core/test_conventions_properties.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Properties the core conventions guarantee (hypothesis).

- A periodic rate converted to continuous compounding and back is unchanged,
  within the rate tolerance.
- For a positive rate, the effective annual rate rises with the compounding
  frequency, and continuous compounding gives the most.
- For a positive rate, the discount factor falls as maturity rises.
- Percent and basis-point conversions round-trip.
"""

from __future__ import annotations

from itertools import pairwise

from hypothesis import given
from hypothesis import strategies as st

from pyeconomics.core import (
    Compounding,
    Frequency,
    Tolerance,
    UnitKind,
    basis_points_to_decimal,
    convert_rate,
    decimal_to_basis_points,
    decimal_to_percent,
    default_tolerance,
    discount_factor,
    effective_annual_rate,
    percent_to_decimal,
)

FREQUENCIES = st.sampled_from(list(Frequency))
COMPOUNDINGS = st.sampled_from(list(Compounding))
# Within ADR-0008's default rate bounds, and above -100% per period for the
# largest frequency in use.
RATES = st.floats(min_value=-0.5, max_value=2.0, allow_nan=False)
POSITIVE_RATES = st.floats(min_value=1e-4, max_value=2.0)
MATURITIES = st.floats(min_value=0.0, max_value=100.0)
GAPS = st.floats(min_value=1e-3, max_value=100.0)
# Two roundings of a float: well inside 1e-15 relative. Values whose
# conversion would be subnormal lose precision, so they are left out.
ROUND_TRIP = Tolerance(abs_tol=0.0, rel_tol=1e-15)
SCALED = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False).filter(
    lambda x: x == 0 or abs(x) > 1e-290
)


def _frequency(compounding: Compounding, frequency: Frequency) -> Frequency | None:
    return frequency if compounding is Compounding.PERIODIC else None


@given(rate=RATES, frequency=FREQUENCIES)
def test_periodic_to_continuous_and_back(rate: float, frequency: Frequency) -> None:
    continuous = convert_rate(
        rate, Compounding.PERIODIC, Compounding.CONTINUOUS, from_frequency=frequency
    )
    back = convert_rate(
        continuous, Compounding.CONTINUOUS, Compounding.PERIODIC, to_frequency=frequency
    )
    assert default_tolerance(UnitKind.RATE).isclose(back, rate)


@given(rate=POSITIVE_RATES)
def test_effective_annual_rate_rises_with_frequency(rate: float) -> None:
    ordered = sorted(Frequency, key=lambda f: f.periods_per_year)
    rates = [effective_annual_rate(rate, Compounding.PERIODIC, f) for f in ordered]
    rates.append(effective_annual_rate(rate, Compounding.CONTINUOUS))
    assert all(low < high for low, high in pairwise(rates))
    assert rates[0] == effective_annual_rate(rate, Compounding.SIMPLE)


@given(
    rate=POSITIVE_RATES,
    years=MATURITIES,
    gap=GAPS,
    compounding=COMPOUNDINGS,
    frequency=FREQUENCIES,
)
def test_discount_factors_fall_as_maturity_rises(
    rate: float,
    years: float,
    gap: float,
    compounding: Compounding,
    frequency: Frequency,
) -> None:
    chosen = _frequency(compounding, frequency)
    nearer = discount_factor(rate, years, compounding, chosen)
    further = discount_factor(rate, years + gap, compounding, chosen)
    assert 0 < further < nearer <= 1


@given(value=SCALED)
def test_percent_conversions_round_trip(value: float) -> None:
    assert ROUND_TRIP.isclose(decimal_to_percent(percent_to_decimal(value)), value)
    assert ROUND_TRIP.isclose(percent_to_decimal(decimal_to_percent(value)), value)


@given(value=SCALED)
def test_basis_point_conversions_round_trip(value: float) -> None:
    assert ROUND_TRIP.isclose(
        decimal_to_basis_points(basis_points_to_decimal(value)), value
    )
    assert ROUND_TRIP.isclose(
        basis_points_to_decimal(decimal_to_basis_points(value)), value
    )
