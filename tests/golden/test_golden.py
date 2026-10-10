# tests/golden/test_golden.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The golden harness over the installed registry (ROADMAP section 5).

From Phase 2 Step 6 on, a model cannot merge unless it has a golden file that
follows the rules in ``_loader.py`` (tests/golden/README.md) and every case in it
runs through ``pyeconomics.run`` within tolerance. ``test_harness.py`` holds the
rules themselves to account with toy models; this module applies them to the real
catalog.

No catalog model is registered yet, so the parametrized test collects no case and
says so in its skip reason; Step 6 adds ``test_registry_is_not_empty``, after
which an empty registry fails.
"""

from __future__ import annotations

import pytest
from _loader import Case, GoldenFile, audit, run_case

import pyeconomics
from pyeconomics.core.registry import installed

REGISTRY = installed()
AUDIT = audit(REGISTRY)

_NONE_YET = pytest.param(
    None,
    None,
    marks=pytest.mark.skip(
        reason="no catalog model is registered yet; Step 6 adds the first golden files"
    ),
    id="no-catalog-model",
)

CASES = [
    pytest.param(golden, case, id=f"{golden.model}::{case.id}")
    for golden in AUDIT.files
    for case in golden.cases
] or [_NONE_YET]


def test_every_golden_file_and_registered_model_follows_the_rules() -> None:
    assert not AUDIT.problems, "\n".join(AUDIT.problems)


@pytest.mark.parametrize(("golden", "case"), CASES)
def test_golden_case(golden: GoldenFile, case: Case) -> None:
    model = REGISTRY.get(golden.model)
    mismatches = run_case(model, case, lambda m, inputs: pyeconomics.run(m.id, inputs))
    assert not mismatches, "\n".join(mismatches)
