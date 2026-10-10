# tests/registry/test_model_call.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Calling a model: validated inputs in, validated outputs out."""

from __future__ import annotations

import math
from typing import Any

import pytest
import toy_models as tm
from pydantic import ValidationError

from pyeconomics.core import (
    InputError,
    MissingOptionalDependencyError,
    Model,
    ModelWarning,
    collect_warnings,
)

ZC = tm.zero_coupon
GOOD: dict[str, Any] = {"face_value": 100, "rate": 0.05, "years": 10}


def test_a_model_is_called_with_fields_a_mapping_or_an_input_model() -> None:
    by_fields = ZC(**GOOD)
    by_mapping = ZC(GOOD)
    by_instance = ZC(tm.ZeroCouponInputs(**GOOD))
    assert by_fields == by_mapping == by_instance
    assert by_fields.price == pytest.approx(100 / 1.05**10)


def test_a_model_knows_its_id_and_version() -> None:
    assert ZC.id == "fixed_income.toy_zero_coupon"
    assert ZC.version == 1
    assert repr(ZC) == "<Model fixed_income.toy_zero_coupon v1>"
    assert isinstance(ZC, Model)


@pytest.mark.parametrize(
    "bad",
    [
        {"rate": 1.5},
        {"rate": -0.6},
        {"face_value": 0},
        {"face_value": 1e13},
        {"years": 101},
        {"years": 0},
    ],
)
def test_out_of_bounds_inputs_are_rejected(bad: dict[str, float]) -> None:
    with pytest.raises(InputError) as caught:
        ZC(**{**GOOD, **bad})
    (field,) = bad
    assert caught.value.errors[0]["loc"] == (field,)
    assert "fixed_income.toy_zero_coupon" in str(caught.value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nan_and_infinity_are_rejected(value: float) -> None:
    with pytest.raises(InputError) as caught:
        ZC(**{**GOOD, "rate": value})
    assert caught.value.errors[0]["loc"] == ("rate",)


def test_a_missing_field_is_rejected() -> None:
    with pytest.raises(InputError) as caught:
        ZC(face_value=100, rate=0.05)
    assert caught.value.errors[0]["type"] == "missing"


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(InputError) as caught:
        ZC(**GOOD, tax_rate=0.3)
    assert caught.value.errors[0]["type"] == "extra_forbidden"


def test_the_wrong_type_is_rejected() -> None:
    with pytest.raises(InputError):
        ZC(**{**GOOD, "rate": "five percent"})


def test_input_error_keeps_the_pydantic_error_as_its_cause() -> None:
    with pytest.raises(InputError) as caught:
        ZC(**{**GOOD, "rate": 9})
    assert isinstance(caught.value.__cause__, ValidationError)
    assert caught.value.validation_error is caught.value.__cause__


def test_inputs_are_immutable() -> None:
    inputs = tm.ZeroCouponInputs(**GOOD)
    with pytest.raises(ValidationError, match="frozen"):
        inputs.rate = 0.1  # type: ignore[misc]
    assert inputs.rate == 0.05
    assert hash(inputs) == hash(tm.ZeroCouponInputs(**GOOD))


def test_outputs_are_immutable() -> None:
    outputs = ZC(**GOOD)
    with pytest.raises(ValidationError, match="frozen"):
        outputs.price = 0.0  # type: ignore[misc]


def test_an_instance_built_without_validation_is_checked_again() -> None:
    sneaky = tm.ZeroCouponInputs.model_construct(face_value=100, rate=9.0, years=10)
    with pytest.raises(InputError):
        ZC(sneaky)


def test_passing_inputs_and_fields_together_is_an_error() -> None:
    with pytest.raises(TypeError, match="not both"):
        ZC(GOOD, rate=0.04)  # type: ignore[call-overload]


def test_the_wrong_input_model_is_rejected() -> None:
    with pytest.raises(InputError):
        ZC(tm.MeanReturnInputs(returns=(0.1,)))  # type: ignore[call-overload]


def bad_compute(_inputs: tm.ZeroCouponInputs) -> tm.ZeroCouponOutputs:
    return tm.ZeroCouponOutputs.model_construct(price=-5.0)


def test_an_out_of_bounds_output_raises_instead_of_returning() -> None:
    broken: Model[Any, Any] = Model(ZC.spec, bad_compute)
    with pytest.raises(ValidationError) as caught:
        broken(**GOOD)
    assert caught.value.errors()[0]["loc"] == ("price",)
    assert type(caught.value) is ValidationError


@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_a_non_finite_output_raises(value: float) -> None:
    def nan_compute(_inputs: tm.ZeroCouponInputs) -> tm.ZeroCouponOutputs:
        return tm.ZeroCouponOutputs.model_construct(price=value)

    broken: Model[Any, Any] = Model(ZC.spec, nan_compute)
    with pytest.raises(ValidationError):
        broken(**GOOD)


def test_a_dict_returned_by_compute_is_validated_as_outputs() -> None:
    def dict_compute(_inputs: tm.ZeroCouponInputs) -> Any:  # noqa: ANN401
        return {"price": 42.0}

    ok: Model[Any, Any] = Model(ZC.spec, dict_compute)
    assert ok(**GOOD).price == 42.0

    def wrong_compute(_inputs: tm.ZeroCouponInputs) -> Any:  # noqa: ANN401
        return 42.0

    wrong: Model[Any, Any] = Model(ZC.spec, wrong_compute)
    with pytest.raises(ValidationError):
        wrong(**GOOD)


def test_a_model_is_immutable() -> None:
    with pytest.raises(AttributeError):
        ZC.spec = tm.time_value.spec  # type: ignore[misc]
    # Python 3.12 raises TypeError here (a frozen slotted dataclass cannot find
    # its own class in super()); 3.13 and later raise FrozenInstanceError.
    with pytest.raises((AttributeError, TypeError)):
        ZC.extra_attribute = 1  # type: ignore[attr-defined]


# --- families of calculations ------------------------------------------------


def test_a_union_is_resolved_on_the_calculation_field() -> None:
    present = tm.time_value(
        calculation="present_value", future_value=100, rate=0.05, years=10
    )
    future = tm.time_value(
        {"calculation": "future_value", "present_value": 100, "rate": 0.05, "years": 10}
    )
    assert isinstance(present, tm.PresentValueOutputs)
    assert isinstance(future, tm.FutureValueOutputs)
    assert present.present_value == pytest.approx(100 / 1.05**10)
    assert future.future_value == pytest.approx(100 * 1.05**10)


def test_an_input_instance_of_a_member_is_accepted() -> None:
    inputs = tm.FutureValueInputs(present_value=100, rate=0.05, years=1)
    result = tm.time_value(inputs)
    assert isinstance(result, tm.FutureValueOutputs)
    assert result.future_value == pytest.approx(105)


def test_an_unknown_calculation_is_rejected() -> None:
    with pytest.raises(InputError) as caught:
        tm.time_value(calculation="net_value", rate=0.05)
    assert caught.value.errors[0]["type"] == "union_tag_invalid"


def test_a_missing_calculation_is_rejected() -> None:
    with pytest.raises(InputError) as caught:
        tm.time_value(future_value=100, rate=0.05, years=1)
    assert caught.value.errors[0]["type"] == "union_tag_not_found"


def test_a_field_of_another_calculation_is_rejected() -> None:
    with pytest.raises(InputError) as caught:
        tm.time_value(
            calculation="present_value", present_value=100, rate=0.05, years=1
        )
    types = {error["type"] for error in caught.value.errors}
    assert types == {"missing", "extra_forbidden"}


# --- array inputs, warnings and extras ---------------------------------------


def test_an_array_input_is_held_as_a_tuple() -> None:
    inputs = tm.MeanReturnInputs.model_validate({"returns": [0.01, 0.02]})
    assert inputs.returns == (0.01, 0.02)
    assert isinstance(inputs.returns, tuple)
    assert hash(inputs) == hash(tm.MeanReturnInputs(returns=(0.01, 0.02)))


def test_array_elements_are_bounded() -> None:
    with pytest.raises(InputError) as caught:
        tm.mean_return(returns=[0.1, -1.5])
    assert caught.value.errors[0]["loc"] == ("returns", 1)


def test_an_array_is_bounded_in_length() -> None:
    with pytest.raises(InputError) as caught:
        tm.mean_return(returns=[0.01] * 253)
    assert caught.value.errors[0]["type"] == "too_long"
    with pytest.raises(InputError) as caught:
        tm.mean_return(returns=[])
    assert caught.value.errors[0]["type"] == "too_short"


def test_a_model_warning_outside_a_run_goes_through_the_warnings_module() -> None:
    with pytest.warns(ModelWarning, match="every return is zero") as caught:
        tm.mean_return(returns=[0.0, 0.0])
    assert isinstance(caught[0].message, ModelWarning)
    assert caught[0].message.code == "all_zero"
    assert caught[0].filename == __file__ or "toy_models" in caught[0].filename


def test_a_model_warning_inside_a_run_is_recorded_not_raised() -> None:
    with collect_warnings() as recorded:
        outputs = tm.mean_return(returns=[0.0, 0.0])
    assert outputs.mean == 0.0
    assert [w.code for w in recorded] == ["all_zero"]


def test_a_model_that_needs_a_missing_extra_names_it() -> None:
    with pytest.raises(MissingOptionalDependencyError) as caught:
        tm.needs_extra(**GOOD)
    assert caught.value.extra == "toy"
    assert "pyeconomics[toy]" in str(caught.value)


def test_compute_receives_validated_inputs() -> None:
    seen: list[object] = []

    def spy(inputs: tm.ZeroCouponInputs) -> tm.ZeroCouponOutputs:
        seen.append(inputs)
        return tm.ZeroCouponOutputs(price=1.0)

    spied: Model[Any, Any] = Model(ZC.spec, spy)
    spied(GOOD)
    assert isinstance(seen[0], tm.ZeroCouponInputs)
