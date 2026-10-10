# src/pyeconomics/models/foundations/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Foundations: the time value of money, returns, risk statistics, tests, simulation.

The five entries every later domain builds on. Each is registered through the
``foundations`` entry point in the ``pyeconomics.models`` group.
"""

from pyeconomics.models.foundations.hypothesis_tests import hypothesis_tests
from pyeconomics.models.foundations.returns import returns
from pyeconomics.models.foundations.risk_statistics import risk_statistics
from pyeconomics.models.foundations.simulation import simulation
from pyeconomics.models.foundations.time_value import time_value

__all__ = ["hypothesis_tests", "returns", "risk_statistics", "simulation", "time_value"]
