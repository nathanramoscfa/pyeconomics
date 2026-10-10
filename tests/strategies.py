# tests/strategies.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Hypothesis strategies that generate valid inputs for any registered model.

:func:`inputs` reads a model's input fields (their unit markers, bounds, maximum
lengths, enums and literals) and returns a strategy of input mappings the model
accepts, one per draw, ready for ``run_model(model, mapping)``. For a model with
several calculations it draws a member of the union, with its ``calculation``
tag. The strategy also draws the model's own examples now and then, so a
realistic input is always in the mix.

Arrays are drawn short (at most :data:`MAX_ITEMS` items, or the field's minimum
length when that is larger) so a contract run stays fast; the bound a field
declares is the one ``registry.validate()`` already holds it to.

A bound on one field cannot say that two fields must agree (a strike below a
spot, an end after a start). When a model validates across fields, register a
strategy for it in :data:`OVERRIDES`; the contract suite then draws from that.
"""

from __future__ import annotations

import datetime as dt
import enum
import math
import string
import types
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Final,
    Literal,
    TypeAliasType,
    Union,
    get_args,
    get_origin,
)

import annotated_types as at
from hypothesis import strategies as st
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pyeconomics.core import DEFAULT_BOUNDS, DEFAULT_DATE_BOUNDS, Unit, UnitKind
from pyeconomics.core.units import MAX_STRING_LENGTH

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from hypothesis.strategies import SearchStrategy

    from pyeconomics.core import Model

__all__ = ["MAX_ITEMS", "MAX_TEXT", "OVERRIDES", "inputs"]

#: The most items a generated array holds, unless the field needs more.
MAX_ITEMS: Final = 12

#: The most characters a generated string holds.
MAX_TEXT: Final = 12

#: Strategies for models whose inputs a field-by-field draw cannot make valid,
#: keyed by model id. Each returns a strategy of input mappings.
OVERRIDES: Final[dict[str, Callable[[], SearchStrategy[dict[str, Any]]]]] = {}

_TEXT_ALPHABET: Final = string.ascii_letters + string.digits + " _-"
_FALLBACK_BOUND: Final = 1e6


@dataclass(frozen=True, slots=True)
class _Limits:
    """What a field's metadata says about its values."""

    low: Any = None
    high: Any = None
    low_open: bool = False
    high_open: bool = False
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    unit: UnitKind | None = None


def _flatten(metadata: Iterable[object]) -> list[object]:
    """Expand ``Field(...)`` objects and grouped constraints into their parts."""
    flat: list[object] = []
    for item in metadata:
        if isinstance(item, FieldInfo):
            flat.extend(_flatten(item.metadata))
        elif isinstance(item, at.GroupedMetadata):
            flat.extend(_flatten(item))
        else:
            flat.append(item)
    return flat


def _limits(metadata: Sequence[object]) -> _Limits:
    """Read the tightest bounds, lengths, pattern and unit out of the metadata."""
    lows: list[tuple[Any, bool]] = [
        (m.ge, False) for m in metadata if isinstance(m, at.Ge)
    ]
    lows += [(m.gt, True) for m in metadata if isinstance(m, at.Gt)]
    highs: list[tuple[Any, bool]] = [
        (m.le, False) for m in metadata if isinstance(m, at.Le)
    ]
    highs += [(m.lt, True) for m in metadata if isinstance(m, at.Lt)]
    low, low_open = max(lows, key=lambda b: (b[0], b[1]), default=(None, False))
    high, high_open = min(highs, key=lambda b: (b[0], not b[1]), default=(None, False))
    mins = [m.min_length for m in metadata if isinstance(m, at.MinLen)]
    maxes = [m.max_length for m in metadata if isinstance(m, at.MaxLen)]
    patterns = [p for m in metadata if (p := getattr(m, "pattern", None)) is not None]
    units = [m.kind for m in metadata if isinstance(m, Unit)]
    return _Limits(
        low=low,
        high=high,
        low_open=low_open,
        high_open=high_open,
        min_length=max(mins) if mins else None,
        max_length=min(maxes) if maxes else None,
        pattern=str(patterns[-1]) if patterns else None,
        unit=units[-1] if units else None,
    )


def _range(limits: _Limits) -> tuple[Any, Any]:
    """Return the field's bounds, filling a missing end from its unit's defaults."""
    low, high = limits.low, limits.high
    default = DEFAULT_BOUNDS.get(limits.unit) if limits.unit is not None else None
    if default is not None:
        low = default.lower if low is None else low
        high = default.upper if high is None else high
    return (
        -_FALLBACK_BOUND if low is None else low,
        _FALLBACK_BOUND if high is None else high,
    )


def _float(limits: _Limits) -> SearchStrategy[float]:
    low, high = _range(limits)
    return st.floats(
        min_value=float(low),
        max_value=float(high),
        exclude_min=limits.low_open,
        exclude_max=limits.high_open,
        allow_nan=False,
        allow_infinity=False,
        allow_subnormal=False,
    )


def _integer(limits: _Limits) -> SearchStrategy[int]:
    low, high = _range(limits)
    smallest = math.ceil(low)
    if limits.low_open and smallest == low:
        smallest += 1
    largest = math.floor(high)
    if limits.high_open and largest == high:
        largest -= 1
    return st.integers(min_value=smallest, max_value=largest)


def _date(limits: _Limits) -> SearchStrategy[dt.date]:
    low = limits.low if isinstance(limits.low, dt.date) else DEFAULT_DATE_BOUNDS.lower
    high = (
        limits.high if isinstance(limits.high, dt.date) else DEFAULT_DATE_BOUNDS.upper
    )
    if limits.low_open:
        low += dt.timedelta(days=1)
    if limits.high_open:
        high -= dt.timedelta(days=1)
    return st.dates(min_value=low, max_value=high)


def _text(limits: _Limits) -> SearchStrategy[str]:
    if limits.pattern is not None:
        return st.from_regex(limits.pattern, fullmatch=True)
    smallest = limits.min_length or 0
    largest = max(smallest, min(limits.max_length or MAX_STRING_LENGTH, MAX_TEXT))
    return st.text(alphabet=_TEXT_ALPHABET, min_size=smallest, max_size=largest)


def _sizes(limits: _Limits) -> tuple[int, int]:
    smallest = limits.min_length or 0
    return smallest, max(smallest, min(limits.max_length or MAX_ITEMS, MAX_ITEMS))


def _unwrap(annotation: object, metadata: list[object]) -> tuple[object, list[object]]:
    """Strip ``Annotated`` wrappers and type aliases, gathering their metadata."""
    while True:
        if isinstance(annotation, TypeAliasType):
            annotation = annotation.__value__
        elif get_origin(annotation) is Annotated:
            args = get_args(annotation)
            annotation = args[0]
            metadata = [*metadata, *_flatten(args[1:])]
        else:
            return annotation, metadata


def _array(annotation: object, limits: _Limits) -> SearchStrategy[Any]:
    args = get_args(annotation)
    if len(args) == 2 and args[1] is Ellipsis:
        smallest, largest = _sizes(limits)
        return st.lists(_strategy(args[0], []), min_size=smallest, max_size=largest)
    return st.tuples(*(_strategy(arg, []) for arg in args))


def _mapping(annotation: object, limits: _Limits) -> SearchStrategy[Any]:
    key, value = get_args(annotation) or (str, str)
    _, largest = _sizes(limits)
    return st.dictionaries(
        _strategy(key, []), _strategy(value, []), max_size=min(largest, 4)
    )


_SCALARS: Final[dict[object, Callable[[_Limits], SearchStrategy[Any]]]] = {
    bool: lambda _: st.booleans(),
    int: _integer,
    float: _float,
    str: _text,
    dt.date: _date,
}


def _structured(
    annotation: object, origin: object, limits: _Limits
) -> SearchStrategy[Any]:
    """Build a strategy for a literal, an enum, a container or a nested model."""
    if origin is Literal:
        return st.sampled_from(get_args(annotation))
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return st.sampled_from([member.value for member in annotation])
    if annotation is tuple or origin is tuple:
        return _array(annotation, limits)
    if annotation is dict or origin is dict:
        return _mapping(annotation, limits)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _fields(annotation)
    msg = f"no strategy for the type {annotation!r}"
    raise TypeError(msg)


def _strategy(annotation: object, metadata: Sequence[object]) -> SearchStrategy[Any]:
    """Build a strategy for one annotation and the metadata that applies to it."""
    annotation, collected = _unwrap(annotation, list(metadata))
    origin = get_origin(annotation)
    if origin in {Union, types.UnionType}:
        return st.one_of(
            *(
                st.none() if member is type(None) else _strategy(member, collected)
                for member in get_args(annotation)
            )
        )
    limits = _limits(collected)
    builder = _SCALARS.get(annotation)
    if builder is not None:
        return builder(limits)
    return _structured(annotation, origin, limits)


def _fields(cls: type[BaseModel]) -> SearchStrategy[dict[str, Any]]:
    """Draw a mapping of field values for one input model."""
    required: dict[str, SearchStrategy[Any]] = {}
    optional: dict[str, SearchStrategy[Any]] = {}
    for name, info in cls.model_fields.items():
        key = info.alias or name
        strategy = _strategy(info.annotation, _flatten(info.metadata))
        # A one-value Literal is a discriminator tag: a union needs it present.
        is_tag = (
            get_origin(info.annotation) is Literal
            and len(get_args(info.annotation)) == 1
        )
        (required if info.is_required() or is_tag else optional)[key] = strategy
    return st.fixed_dictionaries(required, optional=optional)


def inputs(model: Model[Any, Any]) -> SearchStrategy[Mapping[str, Any]]:
    """Return a strategy of valid input mappings for ``model``.

    A model listed in :data:`OVERRIDES` draws from its own strategy. Otherwise
    the draw follows each field's declared bounds, lengths and enums, picks a
    member of a discriminated union, and sometimes returns one of the model's
    examples.

    Raises
    ------
    TypeError
        If a field has a type no strategy covers; ``registry.validate()`` already
        rejects such a field, so this means the model is not valid.
    """
    override = OVERRIDES.get(model.id)
    if override is not None:
        return override()
    generated = st.one_of(
        *(
            _fields(member)
            for member in model.spec.input_models
            if isinstance(member, type) and issubclass(member, BaseModel)
        )
    )
    examples = [dict(example.inputs) for example in model.spec.examples]
    return st.one_of(generated, st.sampled_from(examples)) if examples else generated
