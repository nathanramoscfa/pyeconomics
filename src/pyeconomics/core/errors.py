# src/pyeconomics/core/errors.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The exceptions pyeconomics raises (ADR-0008 decision 13).

Every exception derives from :class:`PyeconomicsError`, so ``except
PyeconomicsError`` catches anything the package raises on purpose. Each also
derives from the built-in exception a Python caller would expect, so code that
catches ``ValueError`` or ``ImportError`` keeps working.

- :class:`InputError`: an input fails validation.
- :class:`DomainError`: valid inputs have no defined result.
- :class:`ConvergenceError`: a numerical method finds no answer.
- :class:`ModelNotFoundError`: no registered model has the id.
- :class:`RegistryError`: the model registry is inconsistent.
- :class:`MissingOptionalDependencyError`: an optional package is missing.

Examples
--------
>>> from pyeconomics.core import DomainError, PyeconomicsError
>>> try:
...     raise DomainError("the required return must exceed the growth rate")
... except PyeconomicsError as error:
...     print(type(error).__name__, error)
DomainError the required return must exceed the growth rate

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import ValidationError
    from pydantic_core import ErrorDetails

__all__ = [
    "ConvergenceError",
    "DomainError",
    "InputError",
    "MissingOptionalDependencyError",
    "ModelNotFoundError",
    "PyeconomicsError",
    "RegistryError",
]


class PyeconomicsError(Exception):
    """Base class of every exception pyeconomics raises on purpose."""


class InputError(PyeconomicsError, ValueError):
    """An input failed validation: wrong type, out of bounds or not finite.

    Parameters
    ----------
    message
        What is wrong, in terms of the caller's input.
    validation_error
        The pydantic error behind it, when pydantic validated the input.

    Examples
    --------
    >>> from pydantic import BaseModel, ValidationError
    >>> class Inputs(BaseModel):
    ...     rate: float
    >>> try:
    ...     Inputs(rate="five percent")
    ... except ValidationError as error:
    ...     wrapped = InputError.from_validation_error(error)
    >>> wrapped.errors[0]["loc"]
    ('rate',)
    >>> isinstance(wrapped, ValueError)
    True

    """

    def __init__(
        self, message: str, *, validation_error: ValidationError | None = None
    ) -> None:
        super().__init__(message)
        self.validation_error = validation_error

    @classmethod
    def from_validation_error(cls, error: ValidationError) -> InputError:
        """Wrap a pydantic ``ValidationError``, keeping it as the cause."""
        wrapped = cls(str(error), validation_error=error)
        wrapped.__cause__ = error
        return wrapped

    @property
    def errors(self) -> list[ErrorDetails]:
        """Pydantic's structured errors, or an empty list without one."""
        if self.validation_error is None:
            return []
        return self.validation_error.errors()


class DomainError(PyeconomicsError, ValueError):
    """Valid inputs leave the model's result as a whole undefined.

    A Gordon growth value with a required return not above the growth rate,
    or a singular covariance matrix, raises this. When only one output is
    undefined and the others are meaningful, the model returns ``None`` for
    that output with a warning instead (ADR-0008 decision 10).
    """


class ConvergenceError(PyeconomicsError, RuntimeError):
    """A numerical method found no answer within its policy's limits."""


class ModelNotFoundError(PyeconomicsError, LookupError):
    """No registered model, or alias, has the requested id.

    Examples
    --------
    >>> error = ModelNotFoundError("fixed_income.no_such_model")
    >>> error.model_id
    'fixed_income.no_such_model'
    >>> str(error)
    "no model is registered with id 'fixed_income.no_such_model'"

    """

    def __init__(self, model_id: str) -> None:
        super().__init__(f"no model is registered with id {model_id!r}")
        self.model_id = model_id


class RegistryError(PyeconomicsError):
    """The model registry is inconsistent: a duplicate or reused id, say."""


class MissingOptionalDependencyError(PyeconomicsError, ImportError):
    """An optional package a feature needs is not installed.

    The message names what to install: the pyeconomics extra when the package
    comes with one, otherwise the package itself.

    Parameters
    ----------
    package
        The import name of the missing package.
    extra
        The pyeconomics extra that installs it, if any.

    Examples
    --------
    >>> print(MissingOptionalDependencyError("statsmodels", extra="econometrics"))
    this feature needs statsmodels; install it with: pip install 'pyeconomics[econometrics]'
    >>> print(MissingOptionalDependencyError("polars"))
    this feature needs polars; install it with: pip install polars

    """  # noqa: E501 - doctest output lines cannot wrap

    def __init__(self, package: str, *, extra: str | None = None) -> None:
        target = f"'pyeconomics[{extra}]'" if extra else package
        super().__init__(
            f"this feature needs {package}; install it with: pip install {target}",
            name=package,
        )
        self.package = package
        self.extra = extra
