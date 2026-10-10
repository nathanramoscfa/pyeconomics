# src/pyeconomics/core/_released.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The released-id ledger (ADR-0003: a released model id is permanent).

Once a release ships a model id, the id is never deleted or given to another
model. A renamed model keeps its old id as an alias. This ledger records every
id a release shipped, so ``registry.validate()`` can fail when one goes missing
or is reused.

A module holds the ledger rather than a data file because the wheel admits only
Python modules under ``pyeconomics/``. It is empty until Phase 2 Step 14 fills
it with a reviewed script at the ``1.0.0a1`` release.

Examples
--------
>>> from pyeconomics.core._released import RELEASED
>>> len(RELEASED)
0
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["RELEASED", "Released"]


@dataclass(frozen=True, slots=True)
class Released:
    """What the ledger records about one released id."""

    canonical_id: str
    """The canonical id the released id named when it shipped. For an id that
    shipped as a model's own id this is the id itself; for one that shipped as
    an alias it is the model's id at that release."""
    first_version: str
    """The first package version that shipped the id, such as ``1.0.0a1``."""


#: Every released id, with the canonical id it named at release and the first
#: package version that shipped it. Empty until Phase 2 Step 14.
RELEASED: Final[Mapping[str, Released]] = MappingProxyType({})
