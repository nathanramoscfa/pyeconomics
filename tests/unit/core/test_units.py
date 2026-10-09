# tests/unit/core/test_units.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Unit kinds, the ``Annotated`` markers and the default bounds table."""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import pytest
from pydantic import BaseModel, Field, ValidationError

from pyeconomics.core import (
    DEFAULT_BOUNDS,
    DEFAULT_DATE_BOUNDS,
    MAX_ARRAY_LENGTH,
    MAX_STRING_LENGTH,
    UNIT_SCHEMA_KEY,
    Bounds,
    Correlation,
    Count,
    DateBounds,
    DateValue,
    Days,
    IndexLevel,
    Money,
    Periods,
    Probability,
    Rate,
    Ratio,
    Return,
    UnitKind,
    Volatility,
    Years,
    default_bounds,
)


class AllUnits(BaseModel):
    rate: Rate
    ret: Return
    money: Money
    years: Years
    days: Days
    periods: Periods
    count: Count
    ratio: Ratio
    probability: Probability
    volatility: Volatility
    correlation: Correlation
    index_level: IndexLevel
    date: DateValue
    rates: list[Rate] = Field(default_factory=list, max_length=3)


VALID: dict[str, Any] = {
    "rate": 0.05,
    "ret": -0.1,
    "money": 100.0,
    "years": 2.5,
    "days": 30,
    "periods": 2.5,
    "count": 3,
    "ratio": 1.5,
    "probability": 0.5,
    "volatility": 0.2,
    "correlation": -0.3,
    "index_level": 4500.0,
    "date": dt.date(2026, 10, 9),
}

EXPECTED_UNITS = {
    "rate": "rate",
    "ret": "return",
    "money": "money",
    "years": "years",
    "days": "days",
    "periods": "periods",
    "count": "count",
    "ratio": "ratio",
    "probability": "probability",
    "volatility": "volatility",
    "correlation": "correlation",
    "index_level": "index_level",
    "date": "date",
}


def test_the_vocabulary_is_closed_and_complete() -> None:
    assert {kind.value for kind in UnitKind} == {
        "rate",
        "return",
        "money",
        "years",
        "days",
        "periods",
        "count",
        "ratio",
        "probability",
        "volatility",
        "correlation",
        "index_level",
        "date",
    }


def test_every_marker_exports_its_unit_to_json_schema() -> None:
    properties = AllUnits.model_json_schema()["properties"]
    for name, unit in EXPECTED_UNITS.items():
        assert properties[name][UNIT_SCHEMA_KEY] == unit, name
    assert properties["rates"]["items"][UNIT_SCHEMA_KEY] == "rate"
    assert properties["rates"]["maxItems"] == 3


def test_valid_values_pass() -> None:
    parsed = AllUnits(**VALID)
    assert parsed.rate == 0.05
    assert parsed.date == dt.date(2026, 10, 9)


@pytest.mark.parametrize(
    "name",
    [
        "rate",
        "ret",
        "money",
        "years",
        "periods",
        "ratio",
        "probability",
        "volatility",
        "correlation",
        "index_level",
    ],
)
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_float_markers_reject_nan_and_infinity(name: str, bad: float) -> None:
    with pytest.raises(ValidationError, match=r"finite_number|finite number"):
        AllUnits.model_validate({**VALID, name: bad})


@pytest.mark.parametrize("name", ["days", "count"])
def test_whole_number_markers_reject_fractions(name: str) -> None:
    with pytest.raises(ValidationError):
        AllUnits.model_validate({**VALID, name: 2.5})


def test_every_numeric_kind_has_default_bounds() -> None:
    numeric = set(UnitKind) - {UnitKind.DATE}
    assert set(DEFAULT_BOUNDS) == numeric
    for kind in numeric:
        assert default_bounds(kind) is DEFAULT_BOUNDS[kind]


def test_dates_have_their_own_bounds() -> None:
    with pytest.raises(KeyError, match="DEFAULT_DATE_BOUNDS"):
        default_bounds(UnitKind.DATE)
    assert DEFAULT_DATE_BOUNDS.lower == dt.date(1900, 1, 1)
    assert DEFAULT_DATE_BOUNDS.upper == dt.date(2200, 12, 31)
    assert DEFAULT_DATE_BOUNDS.contains(dt.date(2026, 10, 9))
    assert not DEFAULT_DATE_BOUNDS.contains(dt.date(1899, 12, 31))


@pytest.mark.parametrize(
    ("kind", "lower", "upper"),
    [
        (UnitKind.RATE, -0.99, 10.0),
        (UnitKind.RETURN, -1.0, 100.0),
        (UnitKind.MONEY, -1e15, 1e15),
        (UnitKind.YEARS, 0.0, 200.0),
        (UnitKind.DAYS, 0.0, 73_050.0),
        (UnitKind.PERIODS, 0.0, 100_000.0),
        (UnitKind.COUNT, 0.0, 1e9),
        (UnitKind.RATIO, -1e6, 1e6),
        (UnitKind.PROBABILITY, 0.0, 1.0),
        (UnitKind.VOLATILITY, 0.0, 10.0),
        (UnitKind.CORRELATION, -1.0, 1.0),
        (UnitKind.INDEX_LEVEL, 0.0, 1e9),
    ],
)
def test_the_bounds_table(kind: UnitKind, lower: float, upper: float) -> None:
    bounds = DEFAULT_BOUNDS[kind]
    assert (bounds.lower, bounds.upper) == (lower, upper)
    assert bounds.upper_inclusive
    assert bounds.lower_inclusive is (kind is not UnitKind.VOLATILITY)


def test_zero_volatility_is_outside_the_default_bounds() -> None:
    volatility = DEFAULT_BOUNDS[UnitKind.VOLATILITY]
    assert not volatility.contains(0.0)
    assert volatility.contains(1e-12)
    assert volatility.contains(10.0)
    assert not volatility.contains(10.000001)


def test_inclusive_and_exclusive_ends() -> None:
    open_interval = Bounds(0.0, 1.0, lower_inclusive=False, upper_inclusive=False)
    assert not open_interval.contains(0.0)
    assert not open_interval.contains(1.0)
    assert open_interval.contains(0.5)
    closed = Bounds(0.0, 1.0)
    assert closed.contains(0.0)
    assert closed.contains(1.0)
    assert not closed.contains(-1e-12)


@pytest.mark.parametrize(
    ("lower", "upper", "message"),
    [
        (-math.inf, 1.0, "finite"),
        (0.0, math.nan, "finite"),
        (1.0, 1.0, "not below"),
        (2.0, 1.0, "not below"),
    ],
)
def test_bounds_reject_infinite_or_inverted_ends(
    lower: float, upper: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        Bounds(lower, upper)


def test_date_bounds_reject_inverted_ends() -> None:
    with pytest.raises(ValueError, match="not before"):
        DateBounds(dt.date(2000, 1, 1), dt.date(1999, 1, 1))


def test_length_limits() -> None:
    assert MAX_ARRAY_LENGTH == 100_000
    assert MAX_STRING_LENGTH == 256
