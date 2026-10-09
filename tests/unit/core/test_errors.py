# tests/unit/core/test_errors.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The exception taxonomy of ADR-0008 decision 13."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from pyeconomics.core import (
    ConvergenceError,
    DomainError,
    InputError,
    MissingOptionalDependencyError,
    ModelNotFoundError,
    PyeconomicsError,
    RegistryError,
)


@pytest.mark.parametrize(
    ("error", "builtin"),
    [
        (InputError, ValueError),
        (DomainError, ValueError),
        (ConvergenceError, RuntimeError),
        (ModelNotFoundError, LookupError),
        (MissingOptionalDependencyError, ImportError),
        (RegistryError, Exception),
    ],
)
def test_every_error_is_a_pyeconomics_error_and_its_builtin(
    error: type[Exception], builtin: type[Exception]
) -> None:
    assert issubclass(error, PyeconomicsError)
    assert issubclass(error, builtin)


class _Inputs(BaseModel):
    rate: float


def test_input_error_wraps_a_validation_error() -> None:
    with pytest.raises(ValidationError) as caught:
        _Inputs(rate="five percent")  # type: ignore[arg-type]
    error = InputError.from_validation_error(caught.value)
    assert error.validation_error is caught.value
    assert error.__cause__ is caught.value
    assert error.errors[0]["loc"] == ("rate",)
    assert "rate" in str(error)


def test_input_error_without_a_validation_error() -> None:
    error = InputError("the seed must be an integer")
    assert error.validation_error is None
    assert error.errors == []
    assert str(error) == "the seed must be an integer"


def test_model_not_found_names_the_id() -> None:
    error = ModelNotFoundError("equity.missing")
    assert error.model_id == "equity.missing"
    assert "'equity.missing'" in str(error)


def test_missing_optional_dependency_names_the_extra() -> None:
    error = MissingOptionalDependencyError("statsmodels", extra="econometrics")
    assert error.package == "statsmodels"
    assert error.name == "statsmodels"
    assert error.extra == "econometrics"
    assert "pip install 'pyeconomics[econometrics]'" in str(error)


def test_missing_optional_dependency_names_the_package_without_an_extra() -> None:
    error = MissingOptionalDependencyError("polars")
    assert error.extra is None
    assert str(error).endswith("pip install polars")


def test_one_except_clause_catches_them_all() -> None:
    for error in (
        InputError("x"),
        DomainError("x"),
        ConvergenceError("x"),
        ModelNotFoundError("x"),
        RegistryError("x"),
        MissingOptionalDependencyError("x"),
    ):
        with pytest.raises(PyeconomicsError):
            raise error
