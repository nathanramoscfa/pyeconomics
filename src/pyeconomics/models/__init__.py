# src/pyeconomics/models/__init__.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The model catalog: one subpackage per domain, one pure function per model.

No model lives here yet; Phase 2 Steps 6 and 8-12 add them. This tree is where
purity is enforced (ADR-0001, ROADMAP section 4 2.2), twice:

- the ``model-purity`` semgrep rule bans I/O, the clock, ``print``, global
  random state and ``warnings.warn`` in any file under it;
- ``tests/registry/test_model_imports.py`` holds every import to an allowlist:
  the standard library's pure modules, NumPy, SciPy, pandas, pydantic,
  ``pyeconomics.core`` and the module's own domain package. One domain never
  imports another; a helper two domains need moves to ``pyeconomics.core``.

A model reports a non-fatal condition through ``pyeconomics.core.warn``, and
imports an extra's library only inside its ``compute``.
"""
