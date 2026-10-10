# tests/contract.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The contract every registered model keeps, checked by fuzzing it.

For inputs the model accepts (``strategies.inputs``), a run must:

- return outputs within their declared bounds (the run validates them, so an
  out-of-bounds output surfaces as pydantic's ``ValidationError``, a bug in the
  model);
- return only finite numbers, or ``None`` for an output that is undefined, with
  a warning that says why (ADR-0008 decision 10);
- raise nothing but :class:`~pyeconomics.core.DomainError` and
  :class:`~pyeconomics.core.ConvergenceError`, and only for a model that lists
  limitations (where it documents when valid inputs have no answer; a reviewer
  reads that they do), and not for every input: some generated input must
  return a result;
- give the same canonical JSON on a second run of the same inputs;
- round-trip: the canonical JSON parses and canonicalizes to the same bytes, and
  running the parsed inputs again gives the same result.

:func:`check_run` holds one input to all of it; :func:`check_model` fuzzes a
model with a bounded number of examples chosen by its cost class.
"""

from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING, Any, Final

from hypothesis import given, settings
from strategies import inputs

from pyeconomics.core import (
    ConvergenceError,
    CostClass,
    DomainError,
    canonical_json,
    run_model,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyeconomics.core import Model
    from pyeconomics.core.results import Result

__all__ = ["EXAMPLES", "check_model", "check_run"]

#: How many inputs the contract draws for a model, by its cost class.
EXAMPLES: Final = {CostClass.INSTANT: 50, CostClass.LIGHT: 25, CostClass.HEAVY: 10}

_FALLBACK_EXAMPLES: Final = 25


def _walk(value: object, path: str) -> list[tuple[str, object]]:
    """Return every leaf of a dumped output with its path."""
    if isinstance(value, dict):
        return [leaf for k, v in value.items() for leaf in _walk(v, f"{path}.{k}")]
    if isinstance(value, list | tuple):
        return [leaf for i, v in enumerate(value) for leaf in _walk(v, f"{path}[{i}]")]
    return [(path, value)]


def _check_values(result: Result[Any, Any]) -> None:
    """Outputs are finite or undefined, and an undefined one comes with a warning."""
    leaves = _walk(result.outputs.model_dump(mode="python"), "outputs")
    non_finite = [
        path
        for path, value in leaves
        if isinstance(value, float) and not math.isfinite(value)
    ]
    assert not non_finite, f"{result.model_id}: non-finite outputs {non_finite}"
    undefined = [path for path, value in leaves if value is None]
    if undefined:
        assert result.warnings, (
            f"{result.model_id}: {undefined} are None but the run recorded no "
            "warning saying why (ADR-0008 decision 10)"
        )


def _check_documented(model: Model[Any, Any], error: Exception) -> None:
    """A model that can raise for valid inputs says so in its limitations."""
    kind = type(error).__name__
    assert model.spec.limitations, (
        f"{model.id}: raised {kind} for valid inputs but lists no limitation that "
        "documents when that happens"
    )
    assert str(error).strip(), f"{model.id}: {kind} has no message"


def check_run(model: Model[Any, Any], raw: Mapping[str, object]) -> bool:
    """Run ``model`` on ``raw`` and hold the run to the contract.

    Returns
    -------
    bool
        ``True`` if the run returned a result, ``False`` if it raised a
        documented error.

    Raises
    ------
    AssertionError
        If the run breaks a clause of the contract.
    Exception
        Whatever the model raised that is not a documented error, with a note
        naming the contract.
    """
    try:
        first = run_model(model, raw)
    except (DomainError, ConvergenceError) as error:
        _check_documented(model, error)
        # An undefined result is as deterministic as a defined one.
        try:
            run_model(model, raw)
        except type(error):
            return False
        msg = f"{model.id}: raised {type(error).__name__} once and not on a rerun"
        raise AssertionError(msg) from error
    except Exception as error:
        error.add_note(
            f"contract: {model.id} may raise only DomainError and ConvergenceError "
            "for valid inputs"
        )
        raise
    _check_values(first)
    text = first.to_json()
    second = run_model(model, raw)
    assert second.to_json() == text, f"{model.id}: two runs differ for {dict(raw)!r}"
    parsed = json.loads(text, parse_int=float)
    assert canonical_json(parsed).decode("utf-8") == text, (
        f"{model.id}: the canonical JSON does not survive a parse"
    )
    rerun = run_model(model, json.loads(text)["inputs"])
    assert rerun.to_json() == text, (
        f"{model.id}: running the parsed inputs of a result does not reproduce it"
    )
    return True


def check_model(model: Model[Any, Any], *, max_examples: int | None = None) -> None:
    """Fuzz ``model`` with generated inputs, holding every run to the contract.

    Parameters
    ----------
    model
        The model to fuzz.
    max_examples
        How many inputs to draw; by default :data:`EXAMPLES` for its cost class.
    """
    cost = model.spec.cost
    count = max_examples or (EXAMPLES[cost] if cost else _FALLBACK_EXAMPLES)

    returned: list[bool] = []

    @settings(max_examples=count, deadline=None)
    @given(inputs(model))
    def fuzz(raw: Mapping[str, object]) -> None:
        returned.append(check_run(model, raw))

    fuzz()
    # A model that raises for every input would pass each clause above without
    # any output ever being checked.
    assert any(returned), (
        f"{model.id}: all {len(returned)} generated inputs raised a documented "
        "error, so no output was checked; DomainError is for inputs with no "
        "defined result, not for every input"
    )
