# tests/registry/test_array_inputs.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Array fields accept lists, tuples, NumPy arrays and Arrow-stream objects."""

from __future__ import annotations

import datetime as dt
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Annotated, Any, get_args

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import Field, TypeAdapter
from pydantic.fields import FieldInfo

from pyeconomics.core import (
    ARRAY_INPUT,
    DEFAULT_BOUNDS,
    DEFAULT_DATE_BOUNDS,
    DateArray,
    DaysArray,
    MissingOptionalDependencyError,
    ModelInputs,
    Money,
    Rate,
    RateArray,
    UnitKind,
    VolatilityArray,
)
from pyeconomics.core.model import ARRAY_KINDS, MAX_ARRAY_INPUT

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import ValidationError as PydanticValidationError


class Rates(ModelInputs):
    rates: RateArray = Field(max_length=5, description="Rates")


class Dates(ModelInputs):
    dates: DateArray = Field(max_length=5, description="Dates")


class Whole(ModelInputs):
    days: DaysArray = Field(max_length=5, description="Days")


class Vols(ModelInputs):
    vols: VolatilityArray = Field(max_length=5, description="Volatilities")


class Custom(ModelInputs):
    amounts: Annotated[
        tuple[Annotated[Money, Field(ge=-10, le=10)], ...], ARRAY_INPUT
    ] = Field(max_length=3, description="Amounts")


def rejected(model: type[ModelInputs], **fields: object) -> PydanticValidationError:
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the type is checked below
        model(**fields)
    error = caught.value
    assert type(error).__name__ == "ValidationError"
    return error  # type: ignore[return-value]


class HasToNumpy:
    """Stands for a pandas, Polars or pyarrow column: it offers ``to_numpy``."""

    def __init__(self, values: list[float]) -> None:
        self.values = values

    def to_numpy(self) -> np.ndarray[Any, Any]:
        return np.array(self.values)


class HasArray:
    """Stands for an object that only offers the ``__array__`` protocol."""

    def __array__(
        self, dtype: object = None, copy: object = None
    ) -> np.ndarray[Any, Any]:
        return np.array([0.1, 0.2])


class ArrowStream:
    """Stands for an object that exposes only the Arrow PyCapsule stream."""

    def __arrow_c_stream__(self, requested_schema: object = None) -> object:
        return object()


class FakeColumn:
    def __len__(self) -> int:
        return 3

    def to_pylist(self) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeTable:
    def __init__(self, columns: int) -> None:
        self.num_columns = columns

    def column(self, _index: int) -> FakeColumn:
        return FakeColumn()


class FrameLike:
    """Stands for a one-column DataFrame: ``to_numpy`` gives shape (n, 1)."""

    def to_numpy(self) -> np.ndarray[Any, Any]:
        return np.array([[0.1], [0.2]])


class WideFrameLike:
    def to_numpy(self) -> np.ndarray[Any, Any]:
        return np.array([[0.1, 0.2], [0.3, 0.4]])


class NullableColumn:
    """Stands for a pyarrow array with nulls: no zero-copy view, but Python values."""

    def to_numpy(self) -> np.ndarray[Any, Any]:
        msg = "Needed to copy 1 chunks with 1 nulls, but zero_copy_only was True"
        raise ValueError(msg)

    def __len__(self) -> int:
        return 2

    def to_pylist(self) -> list[float | None]:
        return [0.1, None]


class RefusingColumn:
    def to_numpy(self) -> np.ndarray[Any, Any]:
        msg = "cannot convert"
        raise ValueError(msg)


def fake_pyarrow(columns: int = 1) -> ModuleType:
    module = ModuleType("pyarrow")
    module.table = lambda _stream: FakeTable(columns)  # type: ignore[attr-defined]
    return module


# --- the shapes an array arrives in ------------------------------------------

SOURCES: list[tuple[str, Callable[[], object], list[float]]] = [
    ("list", lambda: [0.1, 0.2, 0.3], [0.1, 0.2, 0.3]),
    ("tuple", lambda: (0.1, 0.2, 0.3), [0.1, 0.2, 0.3]),
    ("ndarray", lambda: np.array([0.1, 0.2, 0.3]), [0.1, 0.2, 0.3]),
    (
        "float32",
        lambda: np.array([0.5, 0.25, 0.125], dtype=np.float32),
        [0.5, 0.25, 0.125],
    ),
    ("strided view", lambda: np.arange(6, dtype=float)[::2] / 10, [0.0, 0.2, 0.4]),
    ("pandas Series", lambda: pd.Series([0.1, 0.2, 0.3]), [0.1, 0.2, 0.3]),
    ("pandas Index", lambda: pd.Index([0.1, 0.2, 0.3]), [0.1, 0.2, 0.3]),
    ("to_numpy object", lambda: HasToNumpy([0.1, 0.2, 0.3]), [0.1, 0.2, 0.3]),
    ("integers", lambda: np.array([0, 1, 2]), [0.0, 1.0, 2.0]),
]


@pytest.mark.parametrize(
    ("make", "expected"),
    [pytest.param(make, expected, id=name) for name, make, expected in SOURCES],
)
def test_every_array_like_becomes_a_tuple_of_floats(
    make: Callable[[], object], expected: list[float]
) -> None:
    value = Rates(rates=make()).rates  # type: ignore[arg-type]
    assert isinstance(value, tuple)
    assert all(isinstance(item, float) for item in value)
    assert list(value) == expected


def test_an_object_with_array_goes_through_numpy() -> None:
    assert Rates(rates=HasArray()).rates == (0.1, 0.2)  # type: ignore[arg-type]


def test_a_pandas_frame_is_not_one_dimensional() -> None:
    error = rejected(Rates, rates=pd.DataFrame({"a": [0.1], "b": [0.2]}))
    assert "one-dimensional" in str(error)


def test_a_two_dimensional_array_is_rejected() -> None:
    error = rejected(Rates, rates=np.zeros((2, 2)))
    assert "one-dimensional" in str(error)


@pytest.mark.parametrize("value", ["0.1", b"0.1", {"a": 0.1}, 0.1, None])
def test_things_that_are_not_arrays_are_rejected(value: object) -> None:
    rejected(Rates, rates=value)


@pytest.mark.parametrize("value", [{0.1, 0.2}, frozenset({0.1})])
def test_a_set_is_rejected_because_it_has_no_order(value: object) -> None:
    assert "no order" in str(rejected(Rates, rates=value))


def test_nan_and_infinity_in_an_array_are_rejected() -> None:
    for bad in (np.nan, np.inf, -np.inf):
        error = rejected(Rates, rates=np.array([0.1, bad]))
        assert error.errors()[0]["loc"] == ("rates", 1)


def test_elements_outside_the_unit_bounds_are_rejected() -> None:
    assert rejected(Rates, rates=[0.1, 10.5]).errors()[0]["loc"] == ("rates", 1)
    assert rejected(Rates, rates=[-1.0]).errors()[0]["loc"] == ("rates", 0)


def test_the_length_is_bounded_by_the_field() -> None:
    assert rejected(Rates, rates=[0.1] * 6).errors()[0]["type"] == "too_long"
    assert len(Rates.model_validate({"rates": [0.1] * 5}).rates) == 5


def test_a_custom_array_type_takes_its_own_element_bounds() -> None:
    amounts = Custom.model_validate({"amounts": np.array([-10.0, 10.0])}).amounts
    assert amounts == (-10.0, 10.0)
    rejected(Custom, amounts=[11.0])
    rejected(Custom, amounts=[1.0] * 4)


def test_a_boolean_array_is_not_silently_numeric_for_dates() -> None:
    rejected(Dates, dates=np.array([True, False]))


# --- dates and whole numbers -------------------------------------------------


def test_a_datetime64_day_array_becomes_dates() -> None:
    days = np.array(["2026-01-02", "2026-03-04"], dtype="datetime64[D]")
    value = Dates.model_validate({"dates": days})
    assert value.dates == (dt.date(2026, 1, 2), dt.date(2026, 3, 4))


def test_a_nanosecond_datetime_array_becomes_dates() -> None:
    values = np.array(["2026-01-02", "2026-03-04"], dtype="datetime64[ns]")
    found = Dates.model_validate({"dates": values}).dates
    assert found == (dt.date(2026, 1, 2), dt.date(2026, 3, 4))


def test_a_pandas_datetime_series_becomes_dates() -> None:
    series = pd.Series(pd.to_datetime(["2026-01-02", "2026-03-04"]))
    found = Dates.model_validate({"dates": series}).dates
    assert found == (dt.date(2026, 1, 2), dt.date(2026, 3, 4))


def test_dates_outside_the_bounds_are_rejected() -> None:
    rejected(Dates, dates=[dt.date(1850, 1, 1)])
    rejected(Dates, dates=[dt.date(2300, 1, 1)])


def test_a_date_with_a_time_is_rejected() -> None:
    rejected(Dates, dates=np.array(["2026-01-02T12:00"], dtype="datetime64[us]"))


def test_not_a_time_is_rejected() -> None:
    rejected(Dates, dates=np.array(["NaT"], dtype="datetime64[D]"))


def test_whole_numbers_reject_fractions() -> None:
    assert Whole.model_validate({"days": np.array([1, 2, 3])}).days == (1, 2, 3)
    rejected(Whole, days=[1.5])
    rejected(Whole, days=[-1])


def test_volatility_must_be_above_zero() -> None:
    assert Vols.model_validate({"vols": [0.2]}).vols == (0.2,)
    rejected(Vols, vols=[0.0])


# --- Arrow -------------------------------------------------------------------


def test_an_arrow_stream_without_pyarrow_names_the_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pyarrow", None)  # an import raises ImportError
    with pytest.raises(MissingOptionalDependencyError) as caught:
        Rates(rates=ArrowStream())  # type: ignore[arg-type]
    assert caught.value.package == "pyarrow"
    assert str(caught.value).endswith("pip install pyarrow")


def test_an_arrow_stream_is_read_through_pyarrow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pyarrow", fake_pyarrow())
    assert Rates(rates=ArrowStream()).rates == (0.1, 0.2, 0.3)  # type: ignore[arg-type]


def test_an_arrow_table_with_several_columns_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pyarrow", fake_pyarrow(columns=2))
    error = rejected(Rates, rates=ArrowStream())
    assert "expected one column, got 2" in str(error)


def test_a_one_column_table_counts_as_that_column() -> None:
    assert Rates.model_validate({"rates": FrameLike()}).rates == (0.1, 0.2)


def test_a_wide_table_and_a_bare_column_vector_are_rejected() -> None:
    assert "one-column table, got shape (2, 2)" in str(
        rejected(Rates, rates=WideFrameLike())
    )
    rejected(Rates, rates=np.array([[0.1], [0.2]]))  # a bare (n, 1) array stays 2-D


def test_nulls_come_through_as_none_and_are_reported_at_their_index() -> None:
    error = rejected(Rates, rates=NullableColumn())
    assert error.errors()[0]["loc"] == ("rates", 1)
    assert error.errors()[0]["type"] == "float_type"


def test_a_conversion_failure_with_no_python_values_is_reported() -> None:
    assert "cannot convert" in str(rejected(Rates, rates=RefusingColumn()))


def test_a_stream_of_arrays_is_read_as_a_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("pyarrow")

    def refuse(_stream: object) -> object:
        msg = "Cannot import schema: ArrowSchema describes non-struct type double"
        raise ValueError(msg)

    module.table = refuse  # type: ignore[attr-defined]
    module.chunked_array = lambda _stream: FakeColumn()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pyarrow", module)
    assert Rates.model_validate({"rates": ArrowStream()}).rates == (0.1, 0.2, 0.3)


def test_a_huge_year_count_cannot_wrap_into_the_date_bounds() -> None:
    # 6,165,218,490,125 years wraps to 1900 when cast to microseconds.
    wraps = np.array([6165218490125], dtype="datetime64[Y]")
    assert "within 100000 years of 1970" in str(rejected(Dates, dates=wraps))
    wraps_months = np.array([2**62], dtype="datetime64[M]")
    rejected(Dates, dates=wraps_months)


def test_a_huge_day_count_is_a_validation_error_not_an_overflow() -> None:
    error = rejected(Dates, dates=np.array([2**62], dtype="datetime64[D]"))
    assert "within 100000 years of 1970" in str(error)


def test_not_a_time_does_not_trip_the_range_check() -> None:
    values = np.array(["2026-01-02", "NaT"], dtype="datetime64[D]")
    error = rejected(Dates, dates=values)
    assert error.errors()[0]["loc"] == ("dates", 1)


def test_a_datetime_array_without_a_unit_is_rejected() -> None:
    assert "needs a unit" in str(
        rejected(Dates, dates=np.array([], dtype="datetime64"))
    )


def test_an_array_larger_than_the_ceiling_is_refused_before_conversion() -> None:
    huge = np.zeros(MAX_ARRAY_INPUT + 1, dtype=np.int8)
    error = rejected(Whole, days=huge)
    assert f"at most {MAX_ARRAY_INPUT} items" in str(error)


def test_an_arrow_column_larger_than_the_ceiling_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Big:
        def __len__(self) -> int:
            return MAX_ARRAY_INPUT + 1

        def to_pylist(self) -> list[float]:
            msg = "must not be converted"
            raise AssertionError(msg)

    module = ModuleType("pyarrow")
    module.table = lambda _stream: FakeBigTable(Big())  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pyarrow", module)
    assert f"at most {MAX_ARRAY_INPUT} items" in str(
        rejected(Rates, rates=ArrowStream())
    )


class FakeBigTable:
    num_columns = 1

    def __init__(self, column: object) -> None:
        self._column = column

    def column(self, _index: int) -> object:
        return self._column


# --- the aliases -------------------------------------------------------------


def test_there_is_an_array_alias_for_every_unit_kind() -> None:
    assert set(ARRAY_KINDS) == set(DEFAULT_BOUNDS) | {UnitKind.DATE}


@pytest.mark.parametrize("kind", sorted(DEFAULT_BOUNDS, key=str))
def test_each_alias_carries_the_default_bounds_of_its_unit(kind: UnitKind) -> None:
    schema = TypeAdapter(ARRAY_KINDS[kind]).json_schema()  # type: ignore[arg-type]
    items = schema["items"]
    bounds = DEFAULT_BOUNDS[kind]
    assert schema["type"] == "array"
    assert items["x-unit"] == kind.value
    assert items["type"] == (
        "integer" if kind in {UnitKind.DAYS, UnitKind.COUNT} else "number"
    )
    lower = items["minimum"] if bounds.lower_inclusive else items["exclusiveMinimum"]
    assert lower == bounds.lower
    assert items["maximum"] == bounds.upper
    assert "maxItems" not in schema  # the model bounds the length, on the field


def test_the_date_alias_carries_the_default_date_bounds() -> None:
    tuple_type, *_ = get_args(DateArray)
    item = get_args(tuple_type)[0]
    field = next(m for m in get_args(item) if isinstance(m, FieldInfo))
    constraints = {type(c).__name__: c for c in field.metadata}
    assert constraints["Ge"].ge == DEFAULT_DATE_BOUNDS.lower
    assert constraints["Le"].le == DEFAULT_DATE_BOUNDS.upper


# --- the same answer from every shape ----------------------------------------


@given(st.lists(st.floats(-0.9, 9.0), min_size=1, max_size=5))
def test_a_list_a_tuple_and_an_array_give_the_same_inputs(values: list[float]) -> None:
    from_list = Rates.model_validate({"rates": values})
    assert from_list == Rates(rates=tuple(values))
    assert from_list == Rates.model_validate({"rates": np.array(values)})
    assert from_list == Rates.model_validate({"rates": pd.Series(values)})
    assert from_list.rates == tuple(values)


@given(st.lists(st.floats(), min_size=1, max_size=5))
def test_validation_is_the_same_for_a_list_and_an_array(values: list[float]) -> None:
    def accepted(value: object) -> bool:
        try:
            Rates(rates=value)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001 - only acceptance is compared
            return False
        return True

    assert accepted(values) == accepted(np.array(values))


def test_a_scalar_money_field_is_unchanged_by_the_array_machinery() -> None:
    class Plain(ModelInputs):
        rate: Rate = Field(ge=0, le=1, description="A rate")

    assert Plain(rate=0.5).rate == 0.5
