# tests/unit/core/test_tolerance.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Tolerances follow ``math.isclose`` semantics, with defaults per unit kind."""

from __future__ import annotations

import datetime as dt
import math

import pytest

from pyeconomics.core import (
    DEFAULT_TOLERANCES,
    EXACT,
    Tolerance,
    UnitKind,
    default_tolerance,
)


@pytest.mark.parametrize(
    ("actual", "expected", "abs_tol", "rel_tol"),
    [
        (1.0, 1.0 + 1e-10, 0.0, 1e-9),
        (1.0, 1.0 + 1e-8, 0.0, 1e-9),
        (0.0, 1e-13, 1e-12, 0.0),
        (0.0, 1e-11, 1e-12, 0.0),
        (1e6, 1e6 + 0.5, 1.0, 0.0),
        (-5.0, 5.0, 0.0, 1.0),
        (math.inf, math.inf, 0.0, 0.0),
        (math.inf, -math.inf, 1.0, 1.0),
        (math.nan, math.nan, 1.0, 1.0),
    ],
)
def test_isclose_matches_math_isclose(
    actual: float, expected: float, abs_tol: float, rel_tol: float
) -> None:
    tolerance = Tolerance(abs_tol=abs_tol, rel_tol=rel_tol)
    assert tolerance.isclose(actual, expected) is math.isclose(
        actual, expected, abs_tol=abs_tol, rel_tol=rel_tol
    )


def test_the_larger_bound_wins() -> None:
    # |a - b| = 0.01; the relative bound allows 0.0101, the absolute only 0.001.
    assert Tolerance(abs_tol=0.001, rel_tol=0.0001).isclose(101.0, 100.99)
    assert not Tolerance(abs_tol=0.001, rel_tol=0.00001).isclose(101.0, 100.99)


def test_exact_means_equality() -> None:
    assert EXACT.is_exact
    assert EXACT.isclose(0.1 + 0.2, 0.1 + 0.2)
    assert not EXACT.isclose(0.1 + 0.2, 0.3)
    assert not Tolerance().is_exact


def test_dates_and_none_compare_by_equality() -> None:
    day = dt.date(2026, 10, 9)
    assert Tolerance().isclose(day, dt.date(2026, 10, 9))
    assert not Tolerance(abs_tol=10.0).isclose(day, dt.date(2026, 10, 10))
    assert not Tolerance().isclose(day, 0.0)
    assert Tolerance().isclose(None, None)
    assert not Tolerance(abs_tol=1.0).isclose(None, 0.0)
    assert not Tolerance(abs_tol=1.0).isclose(0.0, None)


def test_every_unit_kind_has_a_default() -> None:
    assert set(DEFAULT_TOLERANCES) == set(UnitKind)
    for kind in UnitKind:
        assert default_tolerance(kind) is DEFAULT_TOLERANCES[kind]


@pytest.mark.parametrize(
    "kind",
    [
        UnitKind.RATE,
        UnitKind.RETURN,
        UnitKind.RATIO,
        UnitKind.PROBABILITY,
        UnitKind.VOLATILITY,
        UnitKind.CORRELATION,
    ],
)
def test_decimal_kinds_default_to_1e_12_absolute(kind: UnitKind) -> None:
    assert default_tolerance(kind) == Tolerance(abs_tol=1e-12, rel_tol=1e-9)


@pytest.mark.parametrize("kind", [UnitKind.MONEY, UnitKind.YEARS, UnitKind.INDEX_LEVEL])
def test_level_kinds_default_to_1e_9_absolute(kind: UnitKind) -> None:
    assert default_tolerance(kind) == Tolerance(abs_tol=1e-9, rel_tol=1e-9)


@pytest.mark.parametrize(
    "kind", [UnitKind.PERIODS, UnitKind.COUNT, UnitKind.DAYS, UnitKind.DATE]
)
def test_whole_and_date_kinds_default_to_exact(kind: UnitKind) -> None:
    assert default_tolerance(kind) is EXACT


@pytest.mark.parametrize(
    ("abs_tol", "rel_tol"),
    [(-1e-9, 0.0), (0.0, -1e-9), (math.nan, 0.0), (0.0, math.inf)],
)
def test_tolerances_are_finite_and_not_negative(abs_tol: float, rel_tol: float) -> None:
    with pytest.raises(ValueError, match="finite and not negative"):
        Tolerance(abs_tol=abs_tol, rel_tol=rel_tol)
