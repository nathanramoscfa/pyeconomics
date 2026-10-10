# tests/models/test_contract.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Every registered model keeps the contract in ``tests/contract.py``.

For inputs generated from each model's fields, a run stays within its output
bounds, returns finite numbers or a documented ``None``, raises only the
documented errors, repeats itself exactly and survives a round trip through its
canonical JSON. The inputs per model are bounded by its cost class.

No catalog model is registered yet, so this collects no case and says so in its
skip reason; ``test_contract_rules.py`` holds the checks themselves to account
with toy models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import contract
import pytest

from pyeconomics.core.registry import installed

if TYPE_CHECKING:
    from pyeconomics.core import Model

MODELS = installed().models()

_NONE_YET = pytest.param(
    None,
    marks=pytest.mark.skip(
        reason="no catalog model is registered yet; Step 6 registers the first"
    ),
    id="no-catalog-model",
)


@pytest.mark.parametrize(
    "model", [pytest.param(m, id=m.id) for m in MODELS] or [_NONE_YET]
)
def test_the_model_keeps_the_contract(model: Model[Any, Any]) -> None:
    contract.check_model(model)
