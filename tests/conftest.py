# tests/conftest.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Suite-wide test configuration.

Hypothesis profiles, chosen by the ``HYPOTHESIS_PROFILE`` environment variable
(default ``dev``):

- ``ci``: derandomized, so a CI failure reproduces on any machine; no deadline,
  because shared runners time unevenly; and ``print_blob``, so a failure prints
  the ``@reproduce_failure`` blob.
- ``dev``: hypothesis' defaults, randomized, for local runs.
"""

from __future__ import annotations

import os

from hypothesis import settings

settings.register_profile("ci", derandomize=True, deadline=None, print_blob=True)
settings.register_profile("dev")
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
