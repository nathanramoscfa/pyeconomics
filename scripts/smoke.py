# scripts/smoke.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Smoke-test an installed pyeconomics: import it and exercise the core.

CI runs this script against the built wheel, from a directory outside the
checkout, in a clean virtual environment (ci.yml's ``package`` job) and in
Pyodide (the ``pyodide`` job; ADR-0002, ADR-0008 decision 14). It:

1. imports ``pyeconomics`` and refuses to run when the package resolves
   inside a checkout's ``src/`` tree, so it only ever tests an installed
   distribution;
2. checks ``pyeconomics.__version__`` against the distribution's metadata;
3. converts a monthly rate to its effective annual rate and compares it with
   the closed form;
4. checks the default rate tolerance accepts a rounding error and refuses a
   real difference.

It prints one line per check and exits 0 when every check passes, 1 when one
fails and 2 when it refuses to run. Phase 2 Step 4 extends it to run one
model per domain. Usage, from outside the checkout:

    python smoke.py
"""

from __future__ import annotations

import platform
import sys
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

# (1 + 0.06 / 12) ** 12 - 1, computed independently with 40-digit decimals.
MONTHLY_6_PERCENT_EFFECTIVE = 0.0616778118644995687897


def inside_a_checkout(module_file: str) -> bool:
    """Return whether a package's ``__init__.py`` sits in a checkout's ``src/``."""
    source_tree = Path(module_file).resolve().parent.parent
    return (
        source_tree.name == "src" and (source_tree.parent / "pyproject.toml").is_file()
    )


def check_version(package: ModuleType) -> str:
    """Check the package reports the version in its distribution's metadata."""
    installed = metadata.version("pyeconomics")
    if package.__version__ != installed:
        msg = f"__version__ is {package.__version__}, the metadata says {installed}"
        raise AssertionError(msg)
    return f"__version__ equals the distribution's metadata ({installed})"


def check_compounding(package: ModuleType) -> str:
    """Check 6% compounded monthly is 6.1678% effective annual."""
    core = package.core
    effective = core.convert_rate(
        0.06,
        core.Compounding.PERIODIC,
        core.Compounding.PERIODIC,
        from_frequency=core.Frequency.MONTHLY,
        to_frequency=core.Frequency.ANNUAL,
    )
    tolerance = core.default_tolerance(core.UnitKind.RATE)
    if not tolerance.isclose(effective, MONTHLY_6_PERCENT_EFFECTIVE):
        msg = f"6% monthly gave {effective!r}, not {MONTHLY_6_PERCENT_EFFECTIVE!r}"
        raise AssertionError(msg)
    return f"6% compounded monthly is {core.format_percent(effective, decimals=4)}"


def check_tolerance(package: ModuleType) -> str:
    """Check the rate tolerance accepts rounding and refuses a difference."""
    core = package.core
    tolerance = core.default_tolerance(core.UnitKind.RATE)
    if not tolerance.isclose(0.05, 0.05 + 1e-14):
        msg = "the rate tolerance refuses a 1e-14 rounding error"
        raise AssertionError(msg)
    if tolerance.isclose(0.05, 0.0501):
        msg = "the rate tolerance accepts a 1bp difference"
        raise AssertionError(msg)
    return "the rate tolerance accepts 1e-14 and refuses 1bp"


CHECKS: tuple[tuple[str, Callable[[ModuleType], str]], ...] = (
    ("version", check_version),
    ("compounding", check_compounding),
    ("tolerance", check_tolerance),
)


def main() -> int:
    """Run every check; return the process exit status."""
    import pyeconomics  # noqa: PLC0415 - imported here so a failure is reported
    import pyeconomics.core  # noqa: PLC0415 - loads the core subpackage

    print(
        f"smoke: pyeconomics from {Path(pyeconomics.__file__).parent} on Python "
        f"{platform.python_version()} ({sys.platform})"
    )
    if inside_a_checkout(pyeconomics.__file__):
        print(
            "refused: pyeconomics was imported from a checkout's src/ tree; "
            "install the wheel and run this script from outside the checkout",
            file=sys.stderr,
        )
        return 2
    failed = 0
    for name, check in CHECKS:
        try:
            detail = check(pyeconomics)
        except Exception as error:  # noqa: BLE001 - every failure is reported
            failed += 1
            print(f"FAIL  {name}: {type(error).__name__}: {error}")
        else:
            print(f"ok    {name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
