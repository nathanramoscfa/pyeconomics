# src/pyeconomics/core/model.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The model contract: typed inputs and outputs around a pure ``compute``.

A model is a function from one input model to one output model. The ``@model``
decorator pairs that function with a :class:`~pyeconomics.core.spec.ModelSpec`
and returns a :class:`Model`, which validates the inputs, runs ``compute`` and
validates the outputs. Nothing registers at import time: a package lists its
``Model`` objects in a module's ``__all__`` and names the module in the
``pyeconomics.models`` entry-point group (see :mod:`pyeconomics.core.registry`).

Input and output models derive from :class:`ModelInputs` and
:class:`ModelOutputs`: frozen, closed to unknown fields, and unable to hold NaN
or infinity. A field declares its unit with the markers in
:mod:`pyeconomics.core.units`, its bounds with ``Field(ge=..., le=...)``, and
its description with ``Field(description=...)``. An array field is a tuple whose
elements carry a unit and bounds, and whose length is bounded with
``Field(max_length=...)``; the ``RateArray`` family below is that tuple with the
unit's default element bounds, and :data:`ARRAY_INPUT` builds the rest.

A family whose formulas take different inputs exposes them as a discriminated
union on a ``calculation`` field, with a matching union of outputs.

.. note::

   ``pyeconomics.core`` exports the decorator as ``model``, which hides this
   module's name on the package. Import from the module by path
   (``from pyeconomics.core.model import Model``); ``import
   pyeconomics.core.model as m`` binds the decorator.

Examples
--------
>>> from pydantic import Field
>>> from pyeconomics.core import Money, Rate, Years
>>> from pyeconomics.core.model import ModelInputs, ModelOutputs
>>> class PriceInputs(ModelInputs):
...     face_value: Money = Field(gt=0, le=1e12, description="Face value")
...     rate: Rate = Field(ge=-0.5, le=1.0, description="Annual yield")
...     years: Years = Field(gt=0, le=100, description="Time to maturity")
>>> class PriceOutputs(ModelOutputs):
...     price: Money = Field(ge=0, le=1e14, description="Present value")
>>> PriceInputs(face_value=100, rate=0.05, years=10).years
10.0

"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Final,
    cast,
    get_type_hints,
    overload,
)

import numpy as np
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
)

from pyeconomics.core.errors import InputError, MissingOptionalDependencyError
from pyeconomics.core.spec import Alias, ModelSpec
from pyeconomics.core.units import (
    DEFAULT_DATE_BOUNDS,
    Correlation,
    Count,
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
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from pyeconomics.core.spec import (
        ChangelogEntry,
        ChartSpec,
        CostClass,
        Evidence,
        Example,
        Invariant,
        Reference,
    )

__all__ = [
    "ARRAY_INPUT",
    "ARRAY_KINDS",
    "CorrelationArray",
    "CountArray",
    "DateArray",
    "DaysArray",
    "IndexLevelArray",
    "Model",
    "ModelInputs",
    "ModelOutputs",
    "MoneyArray",
    "PeriodsArray",
    "ProbabilityArray",
    "RateArray",
    "RatioArray",
    "ReturnArray",
    "VolatilityArray",
    "YearsArray",
    "model",
]


class _Closed(BaseModel):
    """What an input or output model has in common: immutable and closed."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        allow_inf_nan=False,
        validate_default=True,
        revalidate_instances="always",
    )


class ModelInputs(_Closed):
    """Base class of a model's inputs.

    Instances are frozen. Unknown fields, NaN and infinity are rejected, and an
    instance passed to a model is validated again, so a value built with
    ``model_construct`` cannot get past the bounds.
    """


class ModelOutputs(_Closed):
    """Base class of a model's outputs, with the same rules as the inputs.

    An output that leaves its bounds is a bug in the model, and raises.
    """


# --- array fields ---------------------------------------------------------


def _ndarray_items(array: np.ndarray[Any, Any], *, table: bool = False) -> list[Any]:
    """Return a one-dimensional array's items as Python values.

    A table (a DataFrame or an Arrow table) with exactly one column counts as
    that column; a bare two-dimensional array does not.
    """
    if table and array.ndim == 2 and array.shape[1] == 1:  # noqa: PLR2004
        array = array[:, 0]
    if array.ndim != 1:
        msg = (
            "expected a one-dimensional array or a one-column table, "
            f"got shape {array.shape}"
        )
        raise ValueError(msg)
    if array.dtype.kind == "M":
        # tolist() turns nanosecond datetimes into integers; microseconds keep
        # the datetime objects pydantic reads as dates.
        array = array.astype("datetime64[us]")
    return array.tolist()  # type: ignore[no-any-return] # NumPy types it as Any


def _arrow_items(stream: object) -> list[Any]:
    """Read a one-column Arrow stream through pyarrow, which the caller owns."""
    try:
        pyarrow = importlib.import_module("pyarrow")
    except ImportError as error:
        package = "pyarrow"
        raise MissingOptionalDependencyError(package) from error
    try:
        table = pyarrow.table(stream)
    except ValueError:
        # A stream of arrays (a column), not of record batches (a table).
        return pyarrow.chunked_array(stream).to_pylist()  # type: ignore[no-any-return]
    if table.num_columns != 1:
        msg = f"expected one column, got {table.num_columns}"
        raise ValueError(msg)
    return table.column(0).to_pylist()  # type: ignore[no-any-return] # pyarrow is Any


def _numpy_items(value: object, to_numpy: Callable[[], object]) -> list[Any]:
    """Read an object through NumPy; nulls it cannot hold come through as None."""
    try:
        array = np.asarray(to_numpy())
    except ValueError:
        # pyarrow refuses a zero-copy view of data with nulls; its Python values
        # carry None, which the field's validation reports at the right index.
        to_pylist = getattr(value, "to_pylist", None)
        if not callable(to_pylist):
            raise
        return to_pylist()  # type: ignore[no-any-return] # pyarrow is Any
    return _ndarray_items(array, table=True)


def _to_sequence(value: object) -> object:
    """Turn an array-like into a list, without copying where the layout allows.

    Lists and tuples pass through. A NumPy array, a pandas or Polars series or
    one-column frame, a pyarrow array, or anything with ``to_numpy`` or
    ``__array__`` goes through NumPy, which shares the buffer; the one copy is
    the Python values the tuple holds. An object that only exposes the Arrow
    PyCapsule stream is read with pyarrow, imported on demand (ADR-0008
    decision 8). Strings, mappings and sets are left for the field's validation
    to reject, because they have no meaningful order.
    """
    if isinstance(value, set | frozenset):
        msg = "an array is ordered; a set has no order"
        raise ValueError(msg)  # noqa: TRY004 - pydantic turns ValueError into an error
    if isinstance(value, str | bytes | bytearray | dict | list | tuple):
        return value
    if isinstance(value, np.ndarray):
        return _ndarray_items(value)
    to_numpy = getattr(value, "to_numpy", None)
    if callable(to_numpy):
        return _numpy_items(value, to_numpy)
    if hasattr(value, "__array__"):
        return _numpy_items(value, lambda: np.asarray(value))
    if hasattr(value, "__arrow_c_stream__"):
        return _arrow_items(value)
    return value


#: The before-validator that makes a tuple field accept the array-likes of
#: ADR-0008 decision 8. Put it last in the ``Annotated`` metadata of a custom
#: array type: ``Annotated[tuple[Annotated[Money, Field(ge=-1e9, le=1e9)], ...],
#: ARRAY_INPUT]``, and bound the length on the field with ``Field(max_length=)``.
ARRAY_INPUT: Final = BeforeValidator(_to_sequence)

# One alias per unit kind, with the kind's default element bounds
# (ADR-0008 decision 3). The bounds are literals because a type alias cannot be
# built by a call; tests pin them to DEFAULT_BOUNDS. The length is the model's
# to bound, on the field, because constraints stacked on one type do not narrow.
RateArray = Annotated[
    tuple[Annotated[Rate, Field(ge=-0.99, le=10.0)], ...], ARRAY_INPUT
]
"""A tuple of rates as decimals."""
ReturnArray = Annotated[
    tuple[Annotated[Return, Field(ge=-1.0, le=100.0)], ...], ARRAY_INPUT
]
"""A tuple of returns as decimals."""
MoneyArray = Annotated[
    tuple[Annotated[Money, Field(ge=-1e15, le=1e15)], ...], ARRAY_INPUT
]
"""A tuple of amounts of money."""
YearsArray = Annotated[
    tuple[Annotated[Years, Field(ge=0.0, le=200.0)], ...], ARRAY_INPUT
]
"""A tuple of times in years."""
DaysArray = Annotated[tuple[Annotated[Days, Field(ge=0, le=73_050)], ...], ARRAY_INPUT]
"""A tuple of whole numbers of days."""
PeriodsArray = Annotated[
    tuple[Annotated[Periods, Field(ge=0.0, le=100_000.0)], ...], ARRAY_INPUT
]
"""A tuple of numbers of periods."""
CountArray = Annotated[
    tuple[Annotated[Count, Field(ge=0, le=1_000_000_000)], ...], ARRAY_INPUT
]
"""A tuple of whole counts."""
RatioArray = Annotated[
    tuple[Annotated[Ratio, Field(ge=-1e6, le=1e6)], ...], ARRAY_INPUT
]
"""A tuple of dimensionless ratios."""
ProbabilityArray = Annotated[
    tuple[Annotated[Probability, Field(ge=0.0, le=1.0)], ...], ARRAY_INPUT
]
"""A tuple of probabilities."""
VolatilityArray = Annotated[
    tuple[Annotated[Volatility, Field(gt=0.0, le=10.0)], ...], ARRAY_INPUT
]
"""A tuple of volatilities, above zero."""
CorrelationArray = Annotated[
    tuple[Annotated[Correlation, Field(ge=-1.0, le=1.0)], ...], ARRAY_INPUT
]
"""A tuple of correlation coefficients."""
IndexLevelArray = Annotated[
    tuple[Annotated[IndexLevel, Field(ge=0.0, le=1e9)], ...], ARRAY_INPUT
]
"""A tuple of index levels."""
DateArray = Annotated[
    tuple[
        Annotated[
            DateValue,
            Field(ge=DEFAULT_DATE_BOUNDS.lower, le=DEFAULT_DATE_BOUNDS.upper),
        ],
        ...,
    ],
    ARRAY_INPUT,
]
"""A tuple of calendar dates."""

#: Each array alias with the unit kind it holds, for tests and tooling.
ARRAY_KINDS: Final = {
    UnitKind.RATE: RateArray,
    UnitKind.RETURN: ReturnArray,
    UnitKind.MONEY: MoneyArray,
    UnitKind.YEARS: YearsArray,
    UnitKind.DAYS: DaysArray,
    UnitKind.PERIODS: PeriodsArray,
    UnitKind.COUNT: CountArray,
    UnitKind.RATIO: RatioArray,
    UnitKind.PROBABILITY: ProbabilityArray,
    UnitKind.VOLATILITY: VolatilityArray,
    UnitKind.CORRELATION: CorrelationArray,
    UnitKind.INDEX_LEVEL: IndexLevelArray,
    UnitKind.DATE: DateArray,
}


# --- the model object -----------------------------------------------------


def _adapter(annotation: object) -> TypeAdapter[Any]:
    return TypeAdapter(cast("Any", annotation))


@dataclass(frozen=True, slots=True, eq=False)
class Model[I: ModelInputs, O: ModelOutputs]:
    """A registered model: its specification and its pure ``compute``.

    Calling the object validates the inputs, runs ``compute`` and validates the
    outputs. It is immutable, and building one has no global effect. Build it
    with the :func:`model` decorator.
    """

    spec: ModelSpec
    """The model's specification."""
    compute: Callable[[I], O]
    """The pure function behind the model. It receives validated inputs."""
    _adapters: dict[str, TypeAdapter[Any]] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> str:
        """The model's permanent id."""
        return self.spec.id

    @property
    def version(self) -> int:
        """The model's version."""
        return self.spec.version

    @property
    def input_adapter(self) -> TypeAdapter[I]:
        """The pydantic adapter that validates inputs and exports their schema."""
        if "inputs" not in self._adapters:
            self._adapters["inputs"] = _adapter(self.spec.inputs)
        return self._adapters["inputs"]

    @property
    def output_adapter(self) -> TypeAdapter[O]:
        """The pydantic adapter that validates outputs and exports their schema."""
        if "outputs" not in self._adapters:
            self._adapters["outputs"] = _adapter(self.spec.outputs)
        return self._adapters["outputs"]

    def validate_inputs(self, inputs: object) -> I:
        """Validate inputs, resolving a union on its ``calculation`` field.

        Parameters
        ----------
        inputs
            An instance of the input model (checked again), or a mapping of
            field values.

        Raises
        ------
        InputError
            If a value is missing, unknown, out of bounds, NaN or infinite. The
            error carries pydantic's details.
        """
        try:
            return self.input_adapter.validate_python(inputs)
        except ValidationError as error:
            msg = f"invalid inputs for model {self.id!r}:\n{error}"
            wrapped = InputError(msg, validation_error=error)
            raise wrapped from error

    def validate_outputs(self, outputs: object) -> O:
        """Validate what ``compute`` returned.

        An output that fails is a bug in the model, not in the caller's input,
        so pydantic's ``ValidationError`` propagates unchanged rather than an
        :class:`~pyeconomics.core.errors.InputError`.
        """
        return self.output_adapter.validate_python(outputs)

    @overload
    def __call__(self, inputs: I, /) -> O: ...

    @overload
    def __call__(self, inputs: Mapping[str, object], /) -> O: ...

    @overload
    def __call__(self, /, **fields: object) -> O: ...

    def __call__(self, inputs: object = None, /, **fields: object) -> O:
        """Run the model on an input model, a mapping, or keyword fields."""
        if inputs is None:
            data: object = fields
        elif fields:
            msg = "pass the inputs as one argument or as keyword fields, not both"
            raise TypeError(msg)
        else:
            data = inputs
        return self.validate_outputs(self.compute(self.validate_inputs(data)))

    def __repr__(self) -> str:
        """Show the id and version."""
        return f"<Model {self.id} v{self.version}>"


def _signature_types(compute: Callable[..., object]) -> tuple[object, object]:
    """Read the input and output types off ``compute``'s type hints."""
    name = getattr(compute, "__qualname__", repr(compute))
    parameters = list(inspect.signature(compute).parameters.values())
    if len(parameters) != 1 or parameters[0].kind not in {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    }:
        msg = f"{name} must take exactly one positional parameter, the inputs"
        raise TypeError(msg)
    try:
        hints = get_type_hints(compute, include_extras=True)
    except NameError as error:
        msg = f"cannot resolve the type hints of {name}: {error}"
        raise TypeError(msg) from error
    inputs = hints.get(parameters[0].name)
    outputs = hints.get("return")
    if inputs is None or outputs is None:
        msg = f"{name} needs type hints on its inputs parameter and its return value"
        raise TypeError(msg)
    return inputs, outputs


def model[I: ModelInputs, O: ModelOutputs](  # noqa: PLR0913 - the spec's fields
    *,
    id: str,  # noqa: A002 - the id is the decorator's name for the model
    version: int,
    title: str,
    summary: str,
    formula: Iterable[str],
    assumptions: Iterable[str],
    limitations: Iterable[str],
    references: Iterable[Reference],
    evidence: Evidence,
    cost: CostClass,
    examples: Iterable[Example],
    changelog: Iterable[ChangelogEntry],
    tags: Iterable[str] = (),
    invariants: Iterable[Invariant] = (),
    no_invariants_reason: str | None = None,
    charts: Iterable[ChartSpec] = (),
    aliases: Sequence[Alias | str] = (),
    extra: str | None = None,
) -> Callable[[Callable[[I], O]], Model[I, O]]:
    """Declare a model: pair a pure function with its specification.

    The decorator reads the input and output types from the function's type
    hints, builds the :class:`~pyeconomics.core.spec.ModelSpec` and returns a
    :class:`Model`. It checks nothing about the specification and registers
    nothing; ``registry.validate()`` rejects an incomplete one.

    Parameters
    ----------
    id
        The permanent dotted id, ``<domain>.<name>``.
    version
        Starts at 1; goes up whenever outputs for some valid input change, or a
        schema changes.
    title, summary
        The card's heading and its one-sentence description.
    formula
        One or more LaTeX strings.
    assumptions, limitations
        What the model takes for granted, and where it stops being valid.
    references
        Sources, each with a DOI or URL and a locator.
    evidence
        How far to trust the model's premise.
    cost
        The compute cost class a hosted service budgets for.
    examples
        Worked inputs the model must accept and run.
    changelog
        One entry per version.
    tags
        Free-form labels.
    invariants, no_invariants_reason
        The properties the model guarantees, or why it declares none.
    charts
        Charts of array outputs.
    aliases
        Retired ids that still resolve, with a warning.
    extra
        The extra whose library ``compute`` imports, if any.
    """

    def decorate(compute: Callable[[I], O]) -> Model[I, O]:
        inputs, outputs = _signature_types(compute)
        spec = ModelSpec(
            id=id,
            version=version,
            title=title,
            summary=summary,
            inputs=inputs,
            outputs=outputs,
            tags=tuple(tags),
            formula=tuple(formula),
            assumptions=tuple(assumptions),
            limitations=tuple(limitations),
            references=tuple(references),
            evidence=evidence,
            cost=cost,
            invariants=tuple(invariants),
            no_invariants_reason=no_invariants_reason,
            examples=tuple(examples),
            charts=tuple(charts),
            aliases=tuple(Alias(id=a) if isinstance(a, str) else a for a in aliases),
            changelog=tuple(changelog),
            extra=extra,
        )
        return Model(spec, compute)

    return decorate
