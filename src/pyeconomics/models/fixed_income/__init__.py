# src/pyeconomics/models/fixed_income/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Fixed income: bond prices and yields, money markets, curves, duration, credit.

The six entries of the launch catalog's fixed-income domain, built on the date
layer in :mod:`pyeconomics.core`. Each is registered through the
``fixed_income`` entry point in the ``pyeconomics.models`` group.
"""

from pyeconomics.models.fixed_income.bond_pricing import bond_pricing
from pyeconomics.models.fixed_income.convexity import convexity
from pyeconomics.models.fixed_income.credit_spread import credit_spread
from pyeconomics.models.fixed_income.curve_bootstrap import curve_bootstrap
from pyeconomics.models.fixed_income.duration import duration
from pyeconomics.models.fixed_income.money_market import money_market

__all__ = [
    "bond_pricing",
    "convexity",
    "credit_spread",
    "curve_bootstrap",
    "duration",
    "money_market",
]
