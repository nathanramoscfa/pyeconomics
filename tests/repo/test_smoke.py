# tests/repo/test_smoke.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""``scripts/smoke.py``: its checks pass, and it refuses a source checkout.

CI runs the script itself against the installed wheel (ci.yml's ``package``
and ``pyodide`` jobs). The test suite imports pyeconomics from the checkout's
``src/`` tree, so here the script must refuse to run, while each of its
checks still passes against this package.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pyeconomics
import pyeconomics.core

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "smoke.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("smoke_script", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


smoke = load_script()


def test_every_check_passes_against_this_package() -> None:
    for name, check in smoke.CHECKS:
        assert isinstance(check(pyeconomics), str), name


def test_it_refuses_the_checkout_src_tree(capsys: pytest.CaptureFixture[str]) -> None:
    assert smoke.inside_a_checkout(pyeconomics.__file__)
    assert smoke.main() == 2
    assert "refused" in capsys.readouterr().err


def test_an_installed_package_is_not_a_checkout(tmp_path: Path) -> None:
    module = tmp_path / "site-packages" / "pyeconomics" / "__init__.py"
    module.parent.mkdir(parents=True)
    module.touch()
    assert not smoke.inside_a_checkout(str(module))
    # A src/ directory without a pyproject.toml beside it is not a checkout.
    other = tmp_path / "src" / "pyeconomics" / "__init__.py"
    other.parent.mkdir(parents=True)
    other.touch()
    assert not smoke.inside_a_checkout(str(other))


def test_it_reports_each_check_and_fails_on_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken(_: ModuleType) -> str:
        msg = "deliberately broken"
        raise AssertionError(msg)

    monkeypatch.setattr(smoke, "inside_a_checkout", lambda _: False)
    monkeypatch.setattr(smoke, "CHECKS", (*smoke.CHECKS, ("broken", broken)))
    assert smoke.main() == 1
    out = capsys.readouterr().out
    assert "ok    version:" in out
    assert "ok    compounding: 6% compounded monthly is 6.1678%" in out
    assert "FAIL  broken: AssertionError: deliberately broken" in out


def test_it_passes_when_every_check_does(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(smoke, "inside_a_checkout", lambda _: False)
    assert smoke.main() == 0
    assert "FAIL" not in capsys.readouterr().out
