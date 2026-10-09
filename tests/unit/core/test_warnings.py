# tests/unit/core/test_warnings.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The warning taxonomy of ADR-0008 decision 13 and ADR-0003."""

from __future__ import annotations

import subprocess  # nosec B404: runs this interpreter with fixed arguments
import sys
import warnings
from pathlib import Path

import pytest

from pyeconomics.core import (
    ModelWarning,
    PyeconomicsDeprecationWarning,
    PyeconomicsWarning,
    deprecated,
    warn,
)


def test_the_hierarchy() -> None:
    assert issubclass(PyeconomicsWarning, UserWarning)
    assert issubclass(ModelWarning, PyeconomicsWarning)
    assert issubclass(PyeconomicsDeprecationWarning, PyeconomicsWarning)
    assert issubclass(PyeconomicsDeprecationWarning, FutureWarning)
    assert not issubclass(PyeconomicsDeprecationWarning, DeprecationWarning)


def test_the_deprecation_warning_is_shown_under_the_default_filters() -> None:
    # A fresh interpreter in isolated mode (-I ignores PYTHONWARNINGS) runs
    # with Python's default warning filters, which hide DeprecationWarning
    # outside __main__ but show FutureWarning.
    code = (
        "import pyeconomics.core as c\n"
        "c.deprecated('old_name', replacement='new_name', removed_in='2.0.0')\n"
    )
    shown = subprocess.run(  # noqa: S603 # nosec B603: fixed arguments, no shell
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "PyeconomicsDeprecationWarning" in shown.stderr
    assert "old_name is deprecated" in shown.stderr
    assert "removed in pyeconomics 2.0.0; use new_name instead" in shown.stderr


def _old_function() -> None:
    deprecated("fixed_income.old", replacement="fixed_income.new", removed_in="2.0.0")


def test_deprecated_names_the_replacement_and_release() -> None:
    with pytest.warns(PyeconomicsDeprecationWarning) as caught:
        _old_function()  # the warning points here, at the deprecated call
    message = caught[0].message
    assert isinstance(message, PyeconomicsDeprecationWarning)
    assert (message.name, message.replacement, message.removed_in) == (
        "fixed_income.old",
        "fixed_income.new",
        "2.0.0",
    )
    assert caught[0].filename == __file__
    source = Path(__file__).read_text(encoding="utf-8").splitlines()
    assert source[caught[0].lineno - 1].strip().startswith("_old_function()")


def test_warn_issues_a_model_warning_with_its_code() -> None:
    with pytest.warns(ModelWarning) as caught:
        warn("undefined_ratio", "the denominator is zero")
    message = caught[0].message
    assert isinstance(message, ModelWarning)
    assert message.code == "undefined_ratio"
    assert message.text == "the denominator is zero"
    assert str(message) == "the denominator is zero [undefined_ratio]"
    assert caught[0].filename == __file__


@pytest.mark.parametrize("code", ["", "Several", "several-roots", "1st", "a b"])
def test_codes_are_snake_case(code: str) -> None:
    with pytest.raises(ValueError, match="snake_case"):
        ModelWarning(code, "message")


def test_model_warnings_are_not_shown_twice_by_default() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("default")
        for _ in range(3):
            warn("same_place", "repeated")
    assert len(caught) == 1
