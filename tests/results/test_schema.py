# tests/results/test_schema.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""JSON Schema export: valid 2020-12 documents that the examples satisfy.

The tests iterate over the installed registry and the toy models, so every
catalog model Steps 6 to 12 register is covered without new test code.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
import toy_models as tm
import toy_results_models as rm
from jsonschema import Draft202012Validator, ValidationError

from pyeconomics import registry
from pyeconomics.core import (
    InputError,
    Model,
    PyeconomicsDeprecationWarning,
    Registry,
    canonical_json,
    input_schema,
    output_schema,
    run_model,
)
from pyeconomics.core import registry as core_registry
from pyeconomics.core.schema import SCHEMA_DIALECT, schema_id

if TYPE_CHECKING:
    from collections.abc import Iterator

TOYS = (*tm.ALL_MODELS, *rm.ALL_MODELS)
MODELS: tuple[Model[Any, Any], ...] = (*registry.models(), *TOYS)
IDS = [f"{m.id}@{m.version}" for m in MODELS]


def numeric_nodes(schema: Any) -> Iterator[dict[str, Any]]:  # noqa: ANN401
    """Yield every schema node that declares a number or integer type."""
    if isinstance(schema, dict):
        if schema.get("type") in {"number", "integer"}:
            yield schema
        for value in schema.values():
            yield from numeric_nodes(value)
    elif isinstance(schema, list):
        for item in schema:
            yield from numeric_nodes(item)


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_both_schemas_are_valid_2020_12_documents(model: Model[Any, Any]) -> None:
    for build in (input_schema, output_schema):
        schema = build(model)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == SCHEMA_DIALECT
        assert schema["title"]
        assert schema["description"] == model.spec.summary
        canonical_json(schema)  # JSON-ready, with finite numbers
        json.loads(json.dumps(schema))


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_the_ids_are_stable_urns(model: Model[Any, Any]) -> None:
    base = f"urn:pyeconomics:model:{model.id}:{model.version}"
    assert input_schema(model)["$id"] == f"{base}:input"
    assert output_schema(model)["$id"] == f"{base}:output"
    assert input_schema(model) == input_schema(model)  # deterministic


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_every_numeric_field_carries_a_unit_and_finite_bounds(
    model: Model[Any, Any],
) -> None:
    for build in (input_schema, output_schema):
        for node in numeric_nodes(build(model)):
            assert "x-unit" in node, node
            assert {"minimum", "exclusiveMinimum"} & set(node), node
            assert {"maximum", "exclusiveMaximum"} & set(node), node


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_each_example_satisfies_the_input_schema(model: Model[Any, Any]) -> None:
    validator = Draft202012Validator(input_schema(model))
    for example in model.spec.examples:
        normalized = model.validate_inputs(example.inputs).model_dump(mode="json")
        validator.validate(normalized)


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_each_examples_outputs_satisfy_the_output_schema(
    model: Model[Any, Any],
) -> None:
    validator = Draft202012Validator(output_schema(model))
    for example in model.spec.examples:
        try:
            result = run_model(model, example.inputs)
        except ImportError:  # a model whose extra is not installed
            continue
        validator.validate(result.to_dict()["outputs"])


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_inputs_survive_canonical_json_losslessly(model: Model[Any, Any]) -> None:
    for example in model.spec.examples:
        original = model.validate_inputs(example.inputs)
        data = canonical_json(original.model_dump(mode="json"))
        revived = model.validate_inputs(json.loads(data))
        assert revived == original
        assert canonical_json(revived.model_dump(mode="json")) == data


@pytest.mark.parametrize("model", MODELS, ids=IDS)
def test_outputs_survive_canonical_json_losslessly(model: Model[Any, Any]) -> None:
    for example in model.spec.examples:
        try:
            outputs = run_model(model, example.inputs).outputs
        except ImportError:
            continue
        data = canonical_json(outputs.model_dump(mode="json"))
        assert model.validate_outputs(json.loads(data)) == outputs


def test_the_input_schema_lists_the_examples_as_the_model_validates_them() -> None:
    schema = input_schema(tm.zero_coupon)
    assert schema["examples"] == [{"face_value": 100.0, "rate": 0.05, "years": 10.0}]
    assert "examples" not in output_schema(tm.zero_coupon)


def test_fields_carry_bounds_descriptions_and_units() -> None:
    properties = input_schema(tm.zero_coupon)["properties"]
    assert properties["rate"] == {
        "description": "Annual yield",
        "maximum": 1.0,
        "minimum": -0.5,
        "title": "Rate",
        "type": "number",
        "x-unit": "rate",
    }
    assert properties["face_value"]["exclusiveMinimum"] == 0
    assert input_schema(tm.zero_coupon)["additionalProperties"] is False
    assert input_schema(tm.zero_coupon)["required"] == ["face_value", "rate", "years"]


def test_an_array_field_is_bounded_and_its_items_have_a_unit() -> None:
    returns = input_schema(tm.mean_return)["properties"]["returns"]
    assert (returns["minItems"], returns["maxItems"]) == (1, 252)
    assert returns["items"]["x-unit"] == "return"
    assert (returns["items"]["minimum"], returns["items"]["maximum"]) == (-1.0, 100.0)


def test_dates_are_date_strings_with_a_unit() -> None:
    start = input_schema(rm.dated)["properties"]["start"]
    assert (start["type"], start["format"], start["x-unit"]) == (
        "string",
        "date",
        "date",
    )


def test_a_nullable_output_keeps_its_unit() -> None:
    per_day = output_schema(rm.dated)["properties"]["per_day"]
    options = per_day["anyOf"]
    assert {"type": "null"} in options
    assert any(option.get("x-unit") == "ratio" for option in options)


def test_a_union_is_one_of_with_a_discriminator_mapping() -> None:
    for build in (input_schema, output_schema):
        schema = build(tm.time_value)
        assert len(schema["oneOf"]) == 2
        assert schema["discriminator"]["propertyName"] == "calculation"
        mapping = schema["discriminator"]["mapping"]
        assert set(mapping) == {"present_value", "future_value"}
        for target in mapping.values():
            assert target.removeprefix("#/$defs/") in schema["$defs"]


def test_a_union_validates_the_right_member_only() -> None:
    validator = Draft202012Validator(input_schema(tm.time_value))
    validator.validate(
        {"calculation": "future_value", "present_value": 1, "rate": 0, "years": 1}
    )
    with pytest.raises(ValidationError):
        validator.validate({"calculation": "future_value", "future_value": 1})
    with pytest.raises(ValidationError):
        validator.validate(
            {"calculation": "present_value", "future_value": 1, "rate": 9, "years": 1}
        )


def test_the_schema_rejects_what_the_model_rejects() -> None:
    validator = Draft202012Validator(input_schema(tm.zero_coupon))
    good = {"face_value": 100, "rate": 0.05, "years": 10}
    validator.validate(good)
    for bad in (
        {**good, "rate": 5},  # 500%, above the model's bound
        {**good, "face_value": 0},
        {**good, "extra": 1},
        {"rate": 0.05},
    ):
        with pytest.raises(ValidationError):
            validator.validate(bad)
        with pytest.raises(InputError):
            tm.zero_coupon.validate_inputs(bad)


def test_an_id_resolves_through_the_installed_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        core_registry._CACHE,  # noqa: SLF001
        "registry",
        Registry.from_models(*tm.ALL_MODELS, distribution="toy", extras=tm.EXTRAS),
    )
    assert input_schema("fixed_income.toy_zero_coupon") == input_schema(tm.zero_coupon)
    with pytest.warns(PyeconomicsDeprecationWarning) as caught:
        schema = output_schema("foundations.toy_tvm")
    assert schema["$id"].endswith("toy_time_value:2:output")
    assert caught[0].filename == __file__


def test_schema_id_names_the_model_version_and_side() -> None:
    assert schema_id("a.b", 3, "output") == "urn:pyeconomics:model:a.b:3:output"
