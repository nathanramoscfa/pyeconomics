# src/pyeconomics/core/tolerance.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Numerical tolerances for outputs (ADR-0008 decision 6).

An output's tolerance is an absolute and a relative bound with the semantics
of :func:`math.isclose`: ``actual`` and ``expected`` agree when

``abs(actual - expected) <= max(rel_tol * max(abs(actual), abs(expected)),
abs_tol)``.

:data:`DEFAULT_TOLERANCES` gives each unit kind a default. A model may
declare its own tolerance for an output, and a golden case may loosen its
tolerance to its source's published precision, recording why.

Examples
--------
>>> from pyeconomics.core import Tolerance, UnitKind, default_tolerance
>>> default_tolerance(UnitKind.RATE).isclose(0.05, 0.05 + 1e-13)
True
>>> Tolerance(abs_tol=0.005).isclose(5.123, 5.12)
True

"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from pyeconomics.core.units import UnitKind

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["DEFAULT_TOLERANCES", "EXACT", "Tolerance", "default_tolerance"]


@dataclass(frozen=True, slots=True)
class Tolerance:
    """An absolute and a relative tolerance, as :func:`math.isclose` uses them.

    Parameters
    ----------
    abs_tol
        The absolute tolerance, zero or more.
    rel_tol
        The relative tolerance, zero or more.

    Raises
    ------
    ValueError
        If either tolerance is negative or not finite.

    """

    abs_tol: float = 0.0
    rel_tol: float = 1e-9

    def __post_init__(self) -> None:
        """Reject negative or non-finite tolerances."""
        for name, value in (("abs_tol", self.abs_tol), ("rel_tol", self.rel_tol)):
            if not (math.isfinite(value) and value >= 0):
                msg = f"{name} must be finite and not negative, not {value!r}"
                raise ValueError(msg)

    @property
    def is_exact(self) -> bool:
        """Whether the tolerance demands equality."""
        return self.abs_tol == 0 and self.rel_tol == 0

    def isclose(
        self, actual: float | dt.date | None, expected: float | dt.date | None
    ) -> bool:
        """Return whether ``actual`` agrees with ``expected``.

        Numbers compare with :func:`math.isclose`, so NaN never agrees and
        an infinity agrees only with itself. Dates and ``None`` (an
        undefined output) compare by equality.

        Examples
        --------
        >>> import datetime as dt
        >>> EXACT.isclose(dt.date(2026, 10, 9), dt.date(2026, 10, 9))
        True
        >>> Tolerance().isclose(None, 0.0)
        False

        """
        if actual is None or expected is None:
            return actual is expected
        if isinstance(actual, dt.date) or isinstance(expected, dt.date):
            return actual == expected
        return math.isclose(
            actual, expected, rel_tol=self.rel_tol, abs_tol=self.abs_tol
        )


#: Equality: no tolerance at all.
EXACT: Final = Tolerance(abs_tol=0.0, rel_tol=0.0)

_DECIMAL = Tolerance(abs_tol=1e-12, rel_tol=1e-9)
_LEVEL = Tolerance(abs_tol=1e-9, rel_tol=1e-9)

#: Default tolerance per unit kind (ADR-0008 decision 6).
DEFAULT_TOLERANCES: Final[Mapping[UnitKind, Tolerance]] = MappingProxyType(
    {
        UnitKind.RATE: _DECIMAL,
        UnitKind.RETURN: _DECIMAL,
        UnitKind.RATIO: _DECIMAL,
        UnitKind.PROBABILITY: _DECIMAL,
        UnitKind.VOLATILITY: _DECIMAL,
        UnitKind.CORRELATION: _DECIMAL,
        UnitKind.MONEY: _LEVEL,
        UnitKind.YEARS: _LEVEL,
        UnitKind.INDEX_LEVEL: _LEVEL,
        UnitKind.PERIODS: EXACT,
        UnitKind.COUNT: EXACT,
        UnitKind.DAYS: EXACT,
        UnitKind.DATE: EXACT,
    }
)


def default_tolerance(kind: UnitKind) -> Tolerance:
    """Return the default tolerance of a unit kind."""
    return DEFAULT_TOLERANCES[kind]
