# src/pyeconomics/core/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The conventions every pyeconomics model encodes (ADR-0008).

This package holds numerical conventions and the date layer: unit kinds and their
default bounds (:mod:`~pyeconomics.core.units`), percent and basis-point
conversion (:mod:`~pyeconomics.core.rates`), compounding
(:mod:`~pyeconomics.core.compounding`), tolerances
(:mod:`~pyeconomics.core.tolerance`), seeded randomness
(:mod:`~pyeconomics.core.random`), root finding
(:mod:`~pyeconomics.core.numerics`), and the error and warning taxonomy
(:mod:`~pyeconomics.core.errors`, :mod:`~pyeconomics.core.warnings`). None of
it does I/O: no network, file, clock or environment access.

Examples
--------
>>> from pyeconomics.core import Compounding, Frequency, discount_factor
>>> round(discount_factor(0.04, 5, Compounding.PERIODIC, Frequency.SEMIANNUAL), 10)
0.8203482999

"""

from pyeconomics.core.calendars import (
    CALENDAR_IDS,
    BusinessDayConvention,
    CalendarId,
    add_business_days,
    adjust,
    is_business_day,
)
from pyeconomics.core.compounding import (
    Compounding,
    Frequency,
    accumulation_factor,
    convert_rate,
    discount_factor,
    effective_annual_rate,
    implied_rate,
)
from pyeconomics.core.dates import (
    actual_days,
    add_months,
    add_years,
    is_end_of_month,
    validate_date,
)
from pyeconomics.core.daycount import DayCount, year_fraction
from pyeconomics.core.errors import (
    ConvergenceError,
    DomainError,
    InputError,
    MissingOptionalDependencyError,
    ModelNotFoundError,
    PyeconomicsError,
    RegistryError,
)
from pyeconomics.core.numerics import (
    DEFAULT_ROOT_POLICY,
    RootPolicy,
    RootResult,
    bracket_roots,
    find_root,
)
from pyeconomics.core.random import (
    BIT_GENERATOR,
    DEFAULT_SEED,
    SEED_MAX,
    SEED_MIN,
    RandomProvenance,
    generator,
    provenance,
)
from pyeconomics.core.rates import (
    BASIS_POINTS_PER_UNIT,
    PERCENT_PER_UNIT,
    basis_points_to_decimal,
    decimal_to_basis_points,
    decimal_to_percent,
    format_basis_points,
    format_percent,
    percent_to_decimal,
)
from pyeconomics.core.schedule import Schedule, generate
from pyeconomics.core.tolerance import (
    DEFAULT_TOLERANCES,
    EXACT,
    Tolerance,
    default_tolerance,
)
from pyeconomics.core.units import (
    DEFAULT_BOUNDS,
    DEFAULT_DATE_BOUNDS,
    MAX_ARRAY_LENGTH,
    MAX_STRING_LENGTH,
    UNIT_SCHEMA_KEY,
    Bounds,
    Correlation,
    Count,
    DateBounds,
    DateValue,
    Days,
    IndexLevel,
    Money,
    Periods,
    Probability,
    Rate,
    Ratio,
    Return,
    Unit,
    UnitKind,
    Volatility,
    Years,
    default_bounds,
)
from pyeconomics.core.warnings import (
    ModelWarning,
    PyeconomicsDeprecationWarning,
    PyeconomicsWarning,
    deprecated,
    warn,
)

__all__ = [
    "BASIS_POINTS_PER_UNIT",
    "BIT_GENERATOR",
    "CALENDAR_IDS",
    "DEFAULT_BOUNDS",
    "DEFAULT_DATE_BOUNDS",
    "DEFAULT_ROOT_POLICY",
    "DEFAULT_SEED",
    "DEFAULT_TOLERANCES",
    "EXACT",
    "MAX_ARRAY_LENGTH",
    "MAX_STRING_LENGTH",
    "PERCENT_PER_UNIT",
    "SEED_MAX",
    "SEED_MIN",
    "UNIT_SCHEMA_KEY",
    "Bounds",
    "BusinessDayConvention",
    "CalendarId",
    "Compounding",
    "ConvergenceError",
    "Correlation",
    "Count",
    "DateBounds",
    "DateValue",
    "DayCount",
    "Days",
    "DomainError",
    "Frequency",
    "IndexLevel",
    "InputError",
    "MissingOptionalDependencyError",
    "ModelNotFoundError",
    "ModelWarning",
    "Money",
    "Periods",
    "Probability",
    "PyeconomicsDeprecationWarning",
    "PyeconomicsError",
    "PyeconomicsWarning",
    "RandomProvenance",
    "Rate",
    "Ratio",
    "RegistryError",
    "Return",
    "RootPolicy",
    "RootResult",
    "Schedule",
    "Tolerance",
    "Unit",
    "UnitKind",
    "Volatility",
    "Years",
    "accumulation_factor",
    "actual_days",
    "add_business_days",
    "add_months",
    "add_years",
    "adjust",
    "basis_points_to_decimal",
    "bracket_roots",
    "convert_rate",
    "decimal_to_basis_points",
    "decimal_to_percent",
    "default_bounds",
    "default_tolerance",
    "deprecated",
    "discount_factor",
    "effective_annual_rate",
    "find_root",
    "format_basis_points",
    "format_percent",
    "generate",
    "generator",
    "implied_rate",
    "is_business_day",
    "is_end_of_month",
    "percent_to_decimal",
    "provenance",
    "validate_date",
    "warn",
    "year_fraction",
]
