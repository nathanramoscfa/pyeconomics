# src/pyeconomics/core/warnings.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The warnings pyeconomics issues (ADR-0008 decision 13; ADR-0003).

- :class:`PyeconomicsWarning` is the base class, a ``UserWarning``.
- :class:`ModelWarning` reports a non-fatal condition in a computation (an
  output left undefined, several roots found) with a stable, machine-readable
  ``code``. Models issue it through :func:`warn`, and the runner records it in
  the result.
- :class:`PyeconomicsDeprecationWarning` announces a removal. It is a
  ``FutureWarning``, so Python shows it by default, and its message names the
  replacement and the release that removes the old name (ADR-0003). Issue it
  through :func:`deprecated`.

Examples
--------
>>> import warnings
>>> from pyeconomics.core import ModelWarning, warn
>>> with warnings.catch_warnings(record=True) as caught:
...     warnings.simplefilter("always")
...     warn("zero_volatility", "the Sharpe ratio is undefined at zero volatility")
>>> caught[0].category is ModelWarning, caught[0].message.code
(True, 'zero_volatility')

"""

from __future__ import annotations

import re
import warnings

__all__ = [
    "ModelWarning",
    "PyeconomicsDeprecationWarning",
    "PyeconomicsWarning",
    "deprecated",
    "warn",
]

_CODE = re.compile(r"[a-z][a-z0-9_]*")


class PyeconomicsWarning(UserWarning):
    """Base class of every warning pyeconomics issues."""


class ModelWarning(PyeconomicsWarning):
    """A non-fatal condition in a model's computation.

    Parameters
    ----------
    code
        A stable snake_case identifier that callers and the result's
        manifest can match on, such as ``"several_roots"``.
    message
        A sentence for people saying what happened and why.

    Raises
    ------
    ValueError
        If ``code`` is not snake_case.

    """

    def __init__(self, code: str, message: str) -> None:
        if not _CODE.fullmatch(code):
            msg = f"a warning code is snake_case, not {code!r}"
            raise ValueError(msg)
        super().__init__(f"{message} [{code}]")
        self.code = code
        self.text = message


class PyeconomicsDeprecationWarning(PyeconomicsWarning, FutureWarning):
    """A public name or behaviour that a named release removes (ADR-0003).

    It subclasses ``FutureWarning``, which Python's default warning filters
    show, unlike ``DeprecationWarning``.

    Parameters
    ----------
    name
        The deprecated name or behaviour.
    replacement
        What to use instead.
    removed_in
        The release that removes it, such as ``"2.0.0"``.

    Examples
    --------
    >>> print(PyeconomicsDeprecationWarning("old_id", replacement="new_id",
    ...                                     removed_in="2.0.0"))
    old_id is deprecated and will be removed in pyeconomics 2.0.0; use new_id instead

    """

    def __init__(self, name: str, *, replacement: str, removed_in: str) -> None:
        super().__init__(
            f"{name} is deprecated and will be removed in pyeconomics "
            f"{removed_in}; use {replacement} instead"
        )
        self.name = name
        self.replacement = replacement
        self.removed_in = removed_in


def warn(code: str, message: str, *, stacklevel: int = 1) -> None:
    """Issue a :class:`ModelWarning` from inside a computation.

    Parameters
    ----------
    code
        The warning's snake_case code.
    message
        What happened, for people.
    stacklevel
        Which frame the warning points at, counted from the code that calls
        :func:`warn`: 1, the default, is that line; 2 is its caller.

    """
    warnings.warn(ModelWarning(code, message), stacklevel=stacklevel + 1)


def deprecated(
    name: str, *, replacement: str, removed_in: str, stacklevel: int = 2
) -> None:
    """Issue a :class:`PyeconomicsDeprecationWarning`.

    Parameters
    ----------
    name
        The deprecated name or behaviour.
    replacement
        What to use instead.
    removed_in
        The release that removes it.
    stacklevel
        Which frame the warning points at, counted from the code that calls
        :func:`deprecated`: 2, the default, is the caller of the deprecated
        function, where the user's code names it.

    Examples
    --------
    >>> import warnings
    >>> with warnings.catch_warnings(record=True) as caught:
    ...     warnings.simplefilter("always")
    ...     deprecated("old_id", replacement="new_id", removed_in="2.0.0")
    >>> issubclass(caught[0].category, FutureWarning)
    True

    """
    warnings.warn(
        PyeconomicsDeprecationWarning(
            name, replacement=replacement, removed_in=removed_in
        ),
        stacklevel=stacklevel + 1,
    )
