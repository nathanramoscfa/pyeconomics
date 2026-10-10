# src/pyeconomics/core/context.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The run context: where a model's warnings go (ADR-0008 decision 13).

A model reports a non-fatal condition through :func:`warn`. What happens next
depends on where the model runs:

- Inside a run, :func:`collect_warnings` has installed a collector. :func:`warn`
  records the :class:`~pyeconomics.core.warnings.ModelWarning` in it and issues
  nothing, so the runner can carry the warnings in the result.
- Outside a run (a model called directly, a doctest, a notebook cell),
  :func:`warn` issues the warning through the :mod:`warnings` module, with the
  stack level pointing at the caller.

The collector lives in a :mod:`contextvars` variable, so concurrent threads and
``asyncio`` tasks each see their own.

Examples
--------
>>> from pyeconomics.core import collect_warnings, warn
>>> with collect_warnings() as recorded:
...     warn("zero_volatility", "the Sharpe ratio is undefined at zero volatility")
>>> [(w.code, w.text) for w in recorded]
[('zero_volatility', 'the Sharpe ratio is undefined at zero volatility')]

"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Final

from pyeconomics.core.warnings import ModelWarning

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["collect_warnings", "warn"]

_COLLECTOR: Final[ContextVar[list[ModelWarning] | None]] = ContextVar(
    "pyeconomics_warning_collector", default=None
)


@contextmanager
def collect_warnings() -> Iterator[list[ModelWarning]]:
    """Record the warnings :func:`warn` issues inside the ``with`` block.

    The runner installs one around each model call. Collectors nest: the
    innermost one receives the warnings, and the outer one is restored on exit.

    Yields
    ------
    list of ModelWarning
        The warnings recorded so far, in the order they were issued.
    """
    recorded: list[ModelWarning] = []
    token = _COLLECTOR.set(recorded)
    try:
        yield recorded
    finally:
        _COLLECTOR.reset(token)


def warn(code: str, message: str, *, stacklevel: int = 1) -> None:
    """Report a non-fatal condition from inside a computation.

    Parameters
    ----------
    code
        The warning's snake_case code. Codes are stable, and each model's card
        documents its own.
    message
        What happened, for people.
    stacklevel
        Which frame the warning points at when it is issued through the
        :mod:`warnings` module, counted from the code that calls :func:`warn`:
        1, the default, is that line; 2 is its caller. A collector ignores it.

    Raises
    ------
    ValueError
        If ``code`` is not snake_case.

    Examples
    --------
    >>> import warnings
    >>> with warnings.catch_warnings(record=True) as caught:
    ...     warnings.simplefilter("always")
    ...     warn("several_roots", "the equation has two roots")
    >>> caught[0].category.__name__, caught[0].message.code
    ('ModelWarning', 'several_roots')

    """
    warning = ModelWarning(code, message)
    collector = _COLLECTOR.get()
    if collector is not None:
        collector.append(warning)
        return
    warnings.warn(warning, stacklevel=stacklevel + 1)
