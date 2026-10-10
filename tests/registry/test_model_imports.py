# tests/registry/test_model_imports.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Purity, second guard: every module under ``models/`` imports only what is allowed.

The ``model-purity`` semgrep rule bans impure *calls*; this test bans impure
*imports*, so a model cannot reach the network, the filesystem or another
domain by a route the rule does not name. It parses each module with ``ast``,
so it holds whatever subset of the suite runs.
"""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "src" / "pyeconomics" / "models"

#: The standard library's pure modules, and ``typing`` machinery. ``datetime``
#: is for types: the semgrep rule bans its clock.
STDLIB = frozenset(
    {
        "__future__",
        "math",
        "cmath",
        "statistics",
        "dataclasses",
        "enum",
        "functools",
        "itertools",
        "operator",
        "collections",
        "typing",
        "decimal",
        "datetime",
    }
)
THIRD_PARTY = frozenset({"numpy", "scipy", "pandas", "pydantic"})
DYNAMIC_IMPORTS = frozenset({"__import__", "import_module"})

Extras = "Mapping[str, frozenset[str]]"


def module_parts(path: Path, models_root: Path = MODELS) -> list[str]:
    """Return the dotted module path of a file under ``models/`` as parts."""
    relative = path.relative_to(models_root).with_suffix("")
    parts = ["pyeconomics", "models", *relative.parts]
    return parts[:-1] if parts[-1] == "__init__" else parts


def domain_of(parts: list[str]) -> str | None:
    """Return the domain package a module belongs to, if it is in one."""
    return parts[2] if len(parts) > 2 else None


def package_of(path: Path, parts: list[str]) -> list[str]:
    """Return the package a module's relative imports start from."""
    return parts if path.name == "__init__.py" else parts[:-1]


def is_model_decorator(node: ast.expr) -> str | None:
    """Return the ``extra`` a ``@model(..., extra="x")`` decorator names."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
    if name != "model":
        return None
    for keyword in node.keywords:
        if (
            keyword.arg == "extra"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        ):
            return keyword.value.value
    return None


class ImportChecker(ast.NodeVisitor):
    """Collect every import the allowlist does not permit."""

    def __init__(
        self,
        parts: list[str],
        package: list[str],
        extra_libraries: Mapping[str, frozenset[str]],
    ) -> None:
        self.parts = parts
        self.package = package
        self.domain = domain_of(parts)
        self.extra_libraries = extra_libraries
        self.extras_in_scope: list[str] = []
        self.problems: list[str] = []

    def allowed(self, target: list[str]) -> bool:
        top = target[0]
        if top in STDLIB or top in THIRD_PARTY:
            return True
        if target[:2] == ["pyeconomics", "core"]:
            return True
        if self.domain is not None and target[:3] == [
            "pyeconomics",
            "models",
            self.domain,
        ]:
            return True
        return any(
            top in self.extra_libraries.get(e, frozenset())
            for e in self.extras_in_scope
        )

    def check(self, target: list[str], line: int) -> None:
        if not self.allowed(target):
            self.problems.append(f"line {line}: imports {'.'.join(target)}")

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.check(alias.name.split("."), node.lineno)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base: list[str] = []
        if node.level:
            keep = len(self.package) - (node.level - 1)
            if keep < 1:
                self.problems.append(
                    f"line {node.lineno}: a relative import leaves the package"
                )
                return
            base = self.package[:keep]
        module = node.module.split(".") if node.module else []
        anchor = [*base, *module]
        if not module or anchor in (["pyeconomics"], ["pyeconomics", "models"]):
            # The names are submodules: `from .. import foundations`.
            for alias in node.names:
                self.check([*anchor, alias.name], node.lineno)
        else:
            self.check(anchor, node.lineno)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        extras = [e for e in map(is_model_decorator, node.decorator_list) if e]
        self.extras_in_scope.extend(extras)
        self.generic_visit(node)
        del self.extras_in_scope[len(self.extras_in_scope) - len(extras) :]

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if name in DYNAMIC_IMPORTS:
            self.problems.append(f"line {node.lineno}: a dynamic import ({name})")
        self.generic_visit(node)


def import_problems(
    source: str,
    path: Path,
    extra_libraries: Mapping[str, frozenset[str]] | None = None,
    models_root: Path = MODELS,
) -> list[str]:
    """Return what is wrong with the imports of one module's source."""
    parts = module_parts(path, models_root)
    checker = ImportChecker(parts, package_of(path, parts), extra_libraries or {})
    checker.visit(ast.parse(source, filename=str(path)))
    return checker.problems


def extras_from_pyproject() -> dict[str, frozenset[str]]:
    """Map each extra to the import names of the packages it installs."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"].get("optional-dependencies", {})
    name = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
    return {
        extra: frozenset(
            match.group().lower().replace("-", "_").replace(".", "_")
            for requirement in requirements
            if (match := name.match(requirement))
        )
        for extra, requirements in extras.items()
    }


# --- the real tree -----------------------------------------------------------

FILES = sorted(MODELS.rglob("*.py"))


def test_the_models_package_exists() -> None:
    assert (MODELS / "__init__.py").is_file()


@pytest.mark.parametrize("path", FILES, ids=[str(p.relative_to(MODELS)) for p in FILES])
def test_a_model_module_imports_only_what_is_allowed(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert import_problems(source, path, extras_from_pyproject()) == []


# --- the checker itself ------------------------------------------------------

DURATION = MODELS / "fixed_income" / "duration.py"
INIT = MODELS / "fixed_income" / "__init__.py"
TOP = MODELS / "__init__.py"


@pytest.mark.parametrize(
    "line",
    [
        "import math",
        "from math import sqrt",
        "import cmath, statistics",
        "from dataclasses import dataclass",
        "from enum import StrEnum",
        "import functools, itertools, operator",
        "from collections import abc",
        "from collections.abc import Sequence",
        "from typing import TYPE_CHECKING",
        "from decimal import Decimal",
        "import datetime",
        "from datetime import date",
        "from __future__ import annotations",
        "import numpy as np",
        "import numpy.typing as npt",
        "from scipy import optimize",
        "from scipy.stats import norm",
        "import pandas as pd",
        "from pydantic import Field",
        "from pyeconomics.core import Rate, model",
        "from pyeconomics.core.units import Money",
        "import pyeconomics.core.numerics",
        "from pyeconomics import core",
        "from pyeconomics.models.fixed_income import helpers",
        "from pyeconomics.models.fixed_income.helpers import accrued",
        "from . import helpers",
        "from .helpers import accrued",
        "from .sub.module import thing",
        "from ...core import units",
    ],
)
def test_allowed_imports_pass(line: str) -> None:
    assert import_problems(line + "\n", DURATION) == []


@pytest.mark.parametrize(
    "line",
    [
        "import os",
        "import sys",
        "import socket",
        "import subprocess",
        "import random",
        "import time",
        "import logging",
        "import pathlib",
        "import json",
        "import requests",
        "import httpx",
        "import statsmodels",
        "from os import environ",
        "from pyeconomics import registry",
        "from pyeconomics import run",
        "import pyeconomics",
        "from pyeconomics.registry import get",
        "from pyeconomics.server import app",
        "from pyeconomics.models.derivatives import forwards",
        "from pyeconomics.models import derivatives",
        "from pyeconomics.models import foundations",
        "from .. import foundations",
        "from ..foundations import returns",
        "import importlib",
        "from importlib import import_module",
    ],
)
def test_disallowed_imports_fail(line: str) -> None:
    assert import_problems(line + "\n", DURATION) != []


def test_one_domain_never_imports_another() -> None:
    source = "from pyeconomics.models.foundations import returns\n"
    [problem] = import_problems(source, DURATION)
    assert "pyeconomics.models.foundations.returns" not in problem
    assert "imports pyeconomics.models.foundations" in problem


def test_a_domain_init_may_list_models_and_share_helpers() -> None:
    source = "from .duration import macaulay\nfrom . import helpers\n"
    assert import_problems(source, INIT) == []


def test_the_models_root_imports_nothing_from_a_domain_but_the_allowlist() -> None:
    assert import_problems("import math\n", TOP) == []
    assert import_problems("from . import fixed_income\n", TOP) != []


def test_a_relative_import_cannot_leave_the_package() -> None:
    [problem] = import_problems("from .... import x\n", DURATION)
    assert "leaves the package" in problem


@pytest.mark.parametrize(
    "call",
    ["__import__('os')", "importlib.import_module('os')", "mod.import_module('os')"],
)
def test_dynamic_imports_fail(call: str) -> None:
    [problem] = import_problems(f"def f():\n    return {call}\n", DURATION)
    assert "dynamic import" in problem


# --- an extra's library ------------------------------------------------------

EXTRAS: Mapping[str, frozenset[str]] = {"econometrics": frozenset({"statsmodels"})}
OLS = MODELS / "econometrics" / "ols.py"

INSIDE_COMPUTE = """
from pyeconomics.core import model


@model(id="econometrics.ols", extra="econometrics")
def ols(inputs):
    import statsmodels.api as sm
    return sm.OLS
"""


def test_an_extras_library_is_allowed_inside_compute() -> None:
    assert import_problems(INSIDE_COMPUTE, OLS, EXTRAS) == []


def test_an_extras_library_is_not_allowed_at_module_level() -> None:
    source = INSIDE_COMPUTE.replace(
        "from pyeconomics.core import model",
        "import statsmodels\nfrom pyeconomics.core import model",
    )
    [problem] = import_problems(source, OLS, EXTRAS)
    assert "imports statsmodels" in problem


def test_an_extras_library_is_not_allowed_in_a_model_that_names_no_extra() -> None:
    source = INSIDE_COMPUTE.replace(', extra="econometrics"', "")
    [problem] = import_problems(source, OLS, EXTRAS)
    assert "imports statsmodels.api" in problem


def test_an_extras_library_is_not_allowed_in_a_model_that_names_another_extra() -> None:
    source = INSIDE_COMPUTE.replace('extra="econometrics"', 'extra="plot"')
    assert import_problems(source, OLS, EXTRAS) != []


def test_an_extras_library_is_not_allowed_in_a_helper_function() -> None:
    source = INSIDE_COMPUTE + "\n\ndef helper():\n    import statsmodels\n"
    [problem] = import_problems(source, OLS, EXTRAS)
    assert "imports statsmodels" in problem


def test_the_extras_come_from_pyproject() -> None:
    extras = extras_from_pyproject()
    assert "econometrics" in extras
    assert all(isinstance(libraries, frozenset) for libraries in extras.values())
