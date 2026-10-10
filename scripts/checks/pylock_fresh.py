# scripts/checks/pylock_fresh.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Fail if pylock.toml is not a fresh export of uv.lock.

pylock.toml (PEP 751) is what pip-audit audits and what tools without uv
install from, so it must say exactly what uv.lock says. This check re-exports
uv.lock without a header and compares it with the committed pylock.toml, whose
leading comment header (the command that wrote it) is ignored. The `uv-lock`
hook checks that uv.lock itself is current.

Usage, from the repository root (the `pylock-fresh` prek hook runs it):

    python scripts/checks/pylock_fresh.py

Re-export with uv's `--no-config` flag, as lock_index.py explains:

    uv export --no-config --all-groups --format pylock.toml --output-file pylock.toml
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 # runs the uv CLI with a fixed argument list
import sys
from pathlib import Path

PYLOCK = Path("pylock.toml")
# Audit every group, including the code-executing documentation toolchain.
EXPORT = (
    "export",
    "--no-config",
    "--frozen",
    "--all-groups",
    "--no-header",
    "--format",
    "pylock.toml",
)
FIX = (
    "uv export --no-config --all-groups --format pylock.toml --output-file pylock.toml"
)


def body(text: str) -> str:
    """Return a lock file without its leading comment header."""
    lines = text.splitlines()
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    return "\n".join(lines).strip()


def export(uv: str) -> str:
    """Return uv.lock exported as pylock.toml, without a header."""
    # bandit B603 / ruff S603: the arguments are fixed, uv is resolved by
    # shutil.which, and no shell is involved.
    result = subprocess.run(  # nosec B603  # noqa: S603
        [uv, *EXPORT], capture_output=True, text=True, encoding="utf-8", check=True
    )
    return result.stdout


def main() -> int:
    """Compare pylock.toml with a fresh export; return the process exit status."""
    uv = shutil.which("uv")
    if uv is None:
        print("pylock-fresh: uv is not on PATH", file=sys.stderr)
        return 1
    if not PYLOCK.is_file():
        print(f"pylock-fresh: {PYLOCK} is missing; run `{FIX}`", file=sys.stderr)
        return 1
    try:
        fresh = export(uv)
    except subprocess.CalledProcessError as error:
        print(f"pylock-fresh: uv export failed:\n{error.stderr}", file=sys.stderr)
        return 1
    if body(PYLOCK.read_text(encoding="utf-8")) != body(fresh):
        print(f"pylock-fresh: {PYLOCK} is stale; run `{FIX}`", file=sys.stderr)
        return 1
    print(f"pylock-fresh: {PYLOCK} matches uv.lock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
