# tests/unit/core/test_rates.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Percent and basis-point conversion and display formatting."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from pyeconomics.core import (
    InputError,
    basis_points_to_decimal,
    decimal_to_basis_points,
    decimal_to_percent,
    format_basis_points,
    format_percent,
    percent_to_decimal,
)

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("percent", "decimal"),
    [(5.0, 0.05), (5.25, 0.0525), (-0.5, -0.005), (0.0, 0.0), (100.0, 1.0)],
)
def test_percent_to_decimal(percent: float, decimal: float) -> None:
    assert percent_to_decimal(percent) == pytest.approx(decimal, rel=1e-15)


@pytest.mark.parametrize(
    ("decimal", "percent"), [(0.05, 5.0), (0.0525, 5.25), (-0.005, -0.5), (1.0, 100.0)]
)
def test_decimal_to_percent(decimal: float, percent: float) -> None:
    assert decimal_to_percent(decimal) == pytest.approx(percent, rel=1e-15)


@pytest.mark.parametrize(
    ("bp", "decimal"), [(125.0, 0.0125), (1.0, 0.0001), (-50.0, -0.005)]
)
def test_basis_points(bp: float, decimal: float) -> None:
    assert basis_points_to_decimal(bp) == pytest.approx(decimal, rel=1e-15)
    assert decimal_to_basis_points(decimal) == pytest.approx(bp, rel=1e-15)


@pytest.mark.parametrize(
    "convert",
    [
        percent_to_decimal,
        decimal_to_percent,
        basis_points_to_decimal,
        decimal_to_basis_points,
    ],
)
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_converters_reject_non_finite_values(
    convert: Callable[[float], float], bad: float
) -> None:
    with pytest.raises(InputError, match="finite"):
        convert(bad)


@pytest.mark.parametrize(
    ("value", "decimals", "shown"),
    [
        (0.0525, 2, "5.25%"),
        (0.05, 0, "5%"),
        (0.123456, 3, "12.346%"),
        (-0.0125, 2, "-1.25%"),
        (-0.00001, 2, "0.00%"),
        (1.0, 1, "100.0%"),
    ],
)
def test_format_percent(value: float, decimals: int, shown: str) -> None:
    assert format_percent(value, decimals=decimals) == shown


@pytest.mark.parametrize(
    ("value", "decimals", "shown"),
    [(0.0125, 0, "125 bp"), (-0.00015, 1, "-1.5 bp"), (-0.000_000_01, 0, "0 bp")],
)
def test_format_basis_points(value: float, decimals: int, shown: str) -> None:
    assert format_basis_points(value, decimals=decimals) == shown


@pytest.mark.parametrize("decimals", [-1, 11])
def test_formatting_refuses_out_of_range_decimals(decimals: int) -> None:
    with pytest.raises(InputError, match="decimals"):
        format_percent(0.05, decimals=decimals)


def test_formatting_refuses_nan() -> None:
    with pytest.raises(InputError, match="finite"):
        format_basis_points(math.nan)
