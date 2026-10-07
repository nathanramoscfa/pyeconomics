# scripts/checks/dist_contents.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Fail if the built wheel or sdist holds a path outside the allowlist.

`uv build` packages what the build backend finds, so a stray `.env`, a
`planning/` file or a test fixture could ship in a release without anyone
reading the archive. This check opens both artifacts in `dist/` and fails on
any member that is not allowlisted, and on a version that differs from
pyproject.toml's. The CI `package` job runs it after `uv build`.

- The wheel holds `pyeconomics/**/*.py`, `pyeconomics/py.typed` and a
  dist-info directory with METADATA, WHEEL, RECORD, LICENSE and NOTICE.
- The sdist holds PKG-INFO, pyproject.toml, README.md, LICENSE, NOTICE and
  `src/pyeconomics/**/*.py` plus `py.typed`, under `pyeconomics-<version>/`.
  It also holds the `pyproject.toml.orig` that uv_build 0.12 always writes,
  allowed only when it is byte-identical to the committed pyproject.toml.

A new kind of packaged file (package data, say) needs an edit here, in the
same change that adds it. That is the point of an allowlist.

Usage, from the repository root:

    uv build
    python scripts/checks/dist_contents.py [DIST_DIR]
"""

from __future__ import annotations

import re
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

PACKAGE = "pyeconomics"
SOURCE = rf"{PACKAGE}(?:/[A-Za-z0-9_]+)*/(?:[A-Za-z0-9_]+\.py|py\.typed)"
TOP_LEVEL = ("PKG-INFO", "pyproject.toml", "README.md", "LICENSE", "NOTICE")


def wheel_allowed(version: str) -> re.Pattern[str]:
    """Return the pattern a wheel member must match."""
    info = re.escape(f"{PACKAGE}-{version}.dist-info")
    return re.compile(
        rf"{PACKAGE}/__init__\.py"
        rf"|{SOURCE}"
        rf"|{info}/(?:METADATA|WHEEL|RECORD)"
        rf"|{info}/licenses/(?:LICENSE|NOTICE)"
    )


def sdist_allowed() -> re.Pattern[str]:
    """Return the pattern an sdist member (below its root) must match."""
    top = "|".join(re.escape(name) for name in TOP_LEVEL)
    return re.compile(rf"{top}|src/{SOURCE}")


def metadata_version(text: str) -> str:
    """Return the Version header of a METADATA or PKG-INFO document."""
    for line in text.splitlines():
        if line.startswith("Version: "):
            return line.removeprefix("Version: ").strip()
    return ""


def check_wheel(path: Path, version: str) -> list[str]:
    """Return the problems with a wheel's members and version."""
    allowed = wheel_allowed(version)
    problems = []
    with zipfile.ZipFile(path) as wheel:
        names = [name for name in wheel.namelist() if not name.endswith("/")]
        problems += [
            f"{path.name}: {name} is not allowlisted"
            for name in names
            if not allowed.fullmatch(name)
        ]
        meta = f"{PACKAGE}-{version}.dist-info/METADATA"
        if meta not in names:
            problems.append(f"{path.name}: {meta} is missing")
        elif (found := metadata_version(wheel.read(meta).decode())) != version:
            problems.append(f"{path.name}: version {found!r}, expected {version!r}")
        problems += [
            f"{path.name}: {required} is missing"
            for required in (f"{PACKAGE}/__init__.py", f"{PACKAGE}/py.typed")
            if required not in names
        ]
    return problems


def check_sdist(path: Path, version: str, pyproject: bytes) -> list[str]:
    """Return the problems with an sdist's members and version."""
    root = f"{PACKAGE}-{version}"
    allowed = sdist_allowed()
    problems = []
    with tarfile.open(path) as sdist:
        files = {m.name: m for m in sdist.getmembers() if m.isfile()}
        for name, member in files.items():
            relative = name.removeprefix(f"{root}/")
            if not name.startswith(f"{root}/"):
                problems.append(f"{path.name}: {name} is outside {root}/")
            elif relative == "pyproject.toml.orig":
                data = sdist.extractfile(member)
                if data is None or data.read() != pyproject:
                    problems.append(
                        f"{path.name}: {relative} differs from pyproject.toml"
                    )
            elif not allowed.fullmatch(relative):
                problems.append(f"{path.name}: {name} is not allowlisted")
        info = files.get(f"{root}/PKG-INFO")
        if info is None:
            problems.append(f"{path.name}: {root}/PKG-INFO is missing")
        elif (data := sdist.extractfile(info)) is not None:
            found = metadata_version(data.read().decode())
            if found != version:
                problems.append(f"{path.name}: version {found!r}, expected {version!r}")
    return problems


def main(root: Path, dist: Path) -> int:
    """Check the artifacts in dist against root's pyproject.toml; return the status."""
    pyproject = (root / "pyproject.toml").read_bytes()
    version = tomllib.loads(pyproject.decode())["project"]["version"]
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        print(
            f"dist-contents: expected one wheel and one sdist in {dist}, "
            f"found {len(wheels)} and {len(sdists)}",
            file=sys.stderr,
        )
        return 1
    problems = check_wheel(wheels[0], version) + check_sdist(
        sdists[0], version, pyproject
    )
    if problems:
        print(
            "dist-contents: the built artifacts hold unexpected content:",
            file=sys.stderr,
        )
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(
        f"dist-contents: {wheels[0].name} and {sdists[0].name} hold only "
        "allowlisted paths."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(Path.cwd(), Path(sys.argv[1] if len(sys.argv) > 1 else "dist")))
