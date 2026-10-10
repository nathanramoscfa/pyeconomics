# tests/models/test_registry_is_not_empty.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The installed registry holds the catalog, so the suites over it check something.

The golden harness and the contract suite parametrize over the installed
registry. If discovery found nothing (a missing entry point, a broken install),
they would collect no case and pass. This test makes an empty registry fail, and
pins the foundations domain Phase 2 Step 6 registered.
"""

from __future__ import annotations

from pyeconomics import registry
from pyeconomics.core import ENTRY_POINT_GROUP
from pyeconomics.core.registry import installed

FOUNDATIONS = {
    "foundations.hypothesis_tests",
    "foundations.returns",
    "foundations.risk_statistics",
    "foundations.simulation",
    "foundations.time_value",
}


def test_the_registry_is_not_empty() -> None:
    assert registry.models(), (
        f"no model is registered; is the package installed with its "
        f"{ENTRY_POINT_GROUP!r} entry points?"
    )


def test_the_foundations_entry_point_registers_its_five_models() -> None:
    assert {m.id for m in registry.models("foundations")} == FOUNDATIONS
    assert "foundations" in registry.domains()


def test_each_foundations_model_comes_from_this_distribution() -> None:
    for registration in installed().registrations:
        if registration.model.id in FOUNDATIONS:
            assert registration.provider.name == "pyeconomics"
