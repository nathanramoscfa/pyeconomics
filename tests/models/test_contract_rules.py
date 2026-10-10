# tests/models/test_contract_rules.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The contract suite holds its own clauses: each one has a model that breaks it.

``test_contract.py`` fuzzes the catalog, which is empty until Step 6. These tests
fuzz the toy models, and rebuild one with a defect for each clause, so the suite
cannot pass vacuously when the catalog arrives.
"""

from __future__ import annotations

import dataclasses
import itertools
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast

import contract
import pytest
import toy_models as tm
import toy_results_models as rm
from pydantic import Field, ValidationError

from pyeconomics.core import (
    CostClass,
    Count,
    Example,
    Model,
    ModelInputs,
    ModelOutputs,
    Money,
    MoneyArray,
    Rate,
    Years,
    model,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class PresentInputs(ModelInputs):
    calculation: Literal["present_value"] = Field(
        default="present_value", description="Discount a future value"
    )
    future_value: Money = Field(ge=0, le=1e6, description="Future value")
    rate: Rate = Field(ge=0, le=0.5, description="Annual rate")
    years: Years = Field(ge=0, le=10, description="Years")


class FutureInputs(ModelInputs):
    calculation: Literal["future_value"] = Field(
        default="future_value", description="Compound a present value"
    )
    present_value: Money = Field(ge=0, le=1e6, description="Present value")
    rate: Rate = Field(ge=0, le=0.5, description="Annual rate")
    years: Years = Field(ge=0, le=10, description="Years")


class PresentOutputs(ModelOutputs):
    calculation: Literal["present_value"] = Field(
        default="present_value", description="Discount a future value"
    )
    present_value: Money = Field(ge=0, le=1e7, description="Present value")


class FutureOutputs(ModelOutputs):
    calculation: Literal["future_value"] = Field(
        default="future_value", description="Compound a present value"
    )
    future_value: Money = Field(ge=0, le=1e8, description="Future value")


@model(
    id="foundations.safe_time_value",
    version=1,
    title="Bounded time value",
    summary="Present and future value with bounds no output can leave.",
    no_invariants_reason="A toy.",
    examples=(
        Example(
            name="discount",
            inputs={
                "calculation": "present_value",
                "future_value": 100,
                "rate": 0.05,
                "years": 3,
            },
        ),
    ),
    **rm.COMMON,
)
def safe_time_value(
    inputs: Annotated[PresentInputs | FutureInputs, Field(discriminator="calculation")],
) -> Annotated[PresentOutputs | FutureOutputs, Field(discriminator="calculation")]:
    growth = (1 + inputs.rate) ** inputs.years
    if isinstance(inputs, PresentInputs):
        return PresentOutputs(present_value=inputs.future_value / growth)
    return FutureOutputs(future_value=inputs.present_value * growth)


class SafeGrowthInputs(ModelInputs):
    start: Money = Field(gt=0, le=1e6, description="Starting balance")
    rate: Rate = Field(ge=-0.5, le=0.5, description="Rate per period")
    periods: Count = Field(ge=1, le=20, description="Number of periods")


class SafeGrowthOutputs(ModelOutputs):
    balance: MoneyArray = Field(max_length=21, description="Balance at each period")
    final: Money = Field(ge=0, le=1e12, description="Final balance")


@model(
    id="foundations.safe_growth",
    version=1,
    title="Bounded growth path",
    summary="A balance compounding at a constant rate, with bounded arrays.",
    no_invariants_reason="A toy.",
    examples=(
        Example(name="three", inputs={"start": 100, "rate": 0.05, "periods": 3}),
    ),
    **rm.COMMON,
)
def safe_growth(inputs: SafeGrowthInputs) -> SafeGrowthOutputs:
    path = tuple(
        inputs.start * (1 + inputs.rate) ** t for t in range(inputs.periods + 1)
    )
    return SafeGrowthOutputs(balance=path, final=path[-1])


GOOD = (
    tm.mean_return,
    safe_time_value,
    safe_growth,
    rm.dated,
    rm.noisy,
    rm.no_chart,
    rm.one_chart,
)

#: Toys whose bounds let an output escape its own: the fuzz finds them, and each
#: has an input that shows it.
LEAKY = (
    (tm.zero_coupon, {"face_value": 1e12, "rate": -0.5, "years": 100}),
    (
        tm.time_value,
        {
            "calculation": "future_value",
            "present_value": 1e12,
            "rate": 1.0,
            "years": 100,
        },
    ),
    (rm.growth, {"start": 1e9, "rate": 1.0, "periods": 40}),
)

ZERO = dict(tm.zero_coupon.spec.examples[0].inputs)
FEW = 15


def rebuilt(
    base: Model[Any, Any], compute: Callable[[Any], Any], **changes: object
) -> Model[Any, Any]:
    """The same model with another ``compute`` and a changed specification."""
    return Model(
        dataclasses.replace(base.spec, **cast("dict[str, Any]", changes)), compute
    )


@pytest.mark.parametrize("model", GOOD, ids=lambda m: m.id)
def test_the_toy_models_keep_the_contract(model: Model[Any, Any]) -> None:
    contract.check_model(model, max_examples=40)


@pytest.mark.parametrize(("model", "raw"), LEAKY, ids=lambda x: getattr(x, "id", ""))
def test_a_model_whose_bounds_let_an_output_escape_fails(
    model: Model[Any, Any], raw: Mapping[str, object]
) -> None:
    with pytest.raises(ValidationError):
        contract.check_run(model, raw)


def test_an_undefined_output_with_a_warning_is_allowed() -> None:
    contract.check_run(rm.dated, {"start": "2026-01-31", "days": 0})


# --- documented errors -------------------------------------------------------------


@pytest.mark.parametrize("mode", ["domain", "convergence"])
def test_a_documented_error_is_allowed(mode: str) -> None:
    contract.check_run(rm.failing, {"x": 0.5, "mode": mode})


@pytest.mark.parametrize("mode", ["domain", "convergence"])
def test_an_error_the_limitations_do_not_document_fails(mode: str) -> None:
    undocumented = rebuilt(rm.failing, rm.failing.compute, limitations=())
    with pytest.raises(AssertionError, match="lists no limitation"):
        contract.check_run(undocumented, {"x": 0.5, "mode": mode})


def test_an_error_without_a_message_fails() -> None:
    from pyeconomics.core import DomainError  # noqa: PLC0415 - beside its use

    def silent(_inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        raise DomainError

    model = rebuilt(tm.zero_coupon, silent)
    with pytest.raises(AssertionError, match="has no message"):
        contract.check_run(model, ZERO)


def test_an_error_that_does_not_repeat_fails() -> None:
    from pyeconomics.core import DomainError  # noqa: PLC0415 - beside its use

    calls = itertools.count()

    def sometimes(inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        if next(calls) == 0:
            msg = "only the first time"
            raise DomainError(msg)
        return tm.ZeroCouponOutputs(price=inputs.face_value)

    with pytest.raises(AssertionError, match="not on a rerun"):
        contract.check_run(rebuilt(tm.zero_coupon, sometimes), ZERO)


def test_any_other_error_fails_with_the_contract_in_a_note() -> None:
    def broken(_inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        msg = "bug"
        raise ValueError(msg)

    with pytest.raises(ValueError, match="bug") as raised:
        contract.check_run(rebuilt(tm.zero_coupon, broken), ZERO)
    assert any("DomainError and ConvergenceError" in n for n in raised.value.__notes__)


def test_an_output_outside_its_bounds_fails() -> None:
    with pytest.raises(ValidationError):
        contract.check_run(rm.failing, {"x": 0.5, "mode": "bad_output"})


def test_a_missing_optional_dependency_is_an_undocumented_error() -> None:
    from pyeconomics.core import MissingOptionalDependencyError  # noqa: PLC0415

    with pytest.raises(MissingOptionalDependencyError):
        contract.check_run(tm.needs_extra, ZERO)


# --- undefined outputs ----------------------------------------------------------


def test_an_undefined_output_needs_a_warning() -> None:
    def quiet(inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        return rm.DatedOutputs(
            end=inputs.start, per_day=None, dates=(inputs.start, inputs.start)
        )

    model = rebuilt(rm.dated, quiet)
    with pytest.raises(AssertionError, match="no warning saying why"):
        contract.check_run(model, {"start": "2026-01-31", "days": 5})


# --- determinism and the round trip ---------------------------------------------


def test_a_model_whose_runs_differ_fails() -> None:
    counter = itertools.count(1)

    def drifting(_inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        return tm.ZeroCouponOutputs(price=float(next(counter)))

    with pytest.raises(AssertionError, match="two runs differ"):
        contract.check_run(rebuilt(tm.zero_coupon, drifting), ZERO)


def test_a_result_that_cannot_be_reproduced_from_its_own_inputs_fails() -> None:
    counter = itertools.count(1)

    def third_time_different(_inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        return tm.ZeroCouponOutputs(price=100.0 if next(counter) % 3 else 200.0)

    model = rebuilt(tm.zero_coupon, third_time_different)
    with pytest.raises(AssertionError, match="does not reproduce it"):
        contract.check_run(model, ZERO)


def test_fuzzing_a_broken_model_fails_the_suite() -> None:
    def broken(_inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        msg = "bug"
        raise ValueError(msg)

    with pytest.raises(ValueError, match="bug"):
        contract.check_model(rebuilt(tm.zero_coupon, broken), max_examples=FEW)


# --- how many inputs ----------------------------------------------------------------


def test_every_cost_class_has_a_bounded_number_of_examples() -> None:
    assert set(contract.EXAMPLES) == set(CostClass)
    assert all(0 < n <= 100 for n in contract.EXAMPLES.values())
    assert (
        contract.EXAMPLES[CostClass.INSTANT]
        >= contract.EXAMPLES[CostClass.LIGHT]
        >= contract.EXAMPLES[CostClass.HEAVY]
    )


def test_a_model_without_a_cost_class_still_gets_a_bounded_run() -> None:
    seen: list[Mapping[str, object]] = []

    def record(inputs: Any) -> Any:  # noqa: ANN401 - a toy compute
        seen.append(inputs.model_dump())
        return tm.ZeroCouponOutputs(price=inputs.face_value)

    model = rebuilt(tm.zero_coupon, record, cost=None)
    contract.check_model(model)
    assert 0 < len(seen) < 1000
