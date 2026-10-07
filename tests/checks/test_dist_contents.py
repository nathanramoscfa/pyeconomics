# tests/checks/test_dist_contents.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for scripts/checks/dist_contents.py, the artifact allowlist."""

from __future__ import annotations

import importlib.util
import io
import tarfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "checks" / "dist_contents.py"
VERSION = "1.0.0.dev1"
PYPROJECT = f'[project]\nname = "pyeconomics"\nversion = "{VERSION}"\n'
INFO = f"pyeconomics-{VERSION}.dist-info"
ROOT = f"pyeconomics-{VERSION}"
METADATA = f"Metadata-Version: 2.4\nName: pyeconomics\nVersion: {VERSION}\n"

WHEEL_FILES = {
    "pyeconomics/__init__.py": "",
    "pyeconomics/py.typed": "",
    f"{INFO}/METADATA": METADATA,
    f"{INFO}/WHEEL": "Wheel-Version: 1.0\n",
    f"{INFO}/RECORD": "",
    f"{INFO}/licenses/LICENSE": "",
    f"{INFO}/licenses/NOTICE": "",
}
SDIST_FILES = {
    f"{ROOT}/PKG-INFO": METADATA,
    f"{ROOT}/pyproject.toml": PYPROJECT,
    f"{ROOT}/pyproject.toml.orig": PYPROJECT,
    f"{ROOT}/README.md": "",
    f"{ROOT}/LICENSE": "",
    f"{ROOT}/NOTICE": "",
    f"{ROOT}/src/pyeconomics/__init__.py": "",
    f"{ROOT}/src/pyeconomics/py.typed": "",
}


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("dist_contents_check", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dist_contents = load_script()


def write_wheel(dist: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(dist / f"pyeconomics-{VERSION}-py3-none-any.whl", "w") as zf:
        for name, text in files.items():
            zf.writestr(name, text)
        zf.writestr("pyeconomics/", "")  # a directory entry, as uv_build writes


def write_sdist(dist: Path, files: dict[str, str]) -> None:
    with tarfile.open(dist / f"pyeconomics-{VERSION}.tar.gz", "w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
        directory = tarfile.TarInfo(ROOT)
        directory.type = tarfile.DIRTYPE
        tar.addfile(directory)


def build(
    tmp_path: Path,
    wheel: dict[str, str] | None = None,
    sdist: dict[str, str] | None = None,
) -> Path:
    root = tmp_path / "repo"
    dist = root / "dist"
    dist.mkdir(parents=True)
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8", newline="\n")
    write_wheel(dist, WHEEL_FILES if wheel is None else wheel)
    write_sdist(dist, SDIST_FILES if sdist is None else sdist)
    return root


def run(root: Path) -> int:
    return int(dist_contents.main(root, root / "dist"))


def test_clean_artifacts_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(build(tmp_path)) == 0
    assert "only allowlisted paths" in capsys.readouterr().out


def test_wheel_with_a_stray_file_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = build(tmp_path, wheel={**WHEEL_FILES, "pyeconomics/.env": "KEY=1"})
    assert run(root) == 1
    assert "pyeconomics/.env is not allowlisted" in capsys.readouterr().err


def test_wheel_with_a_top_level_module_fails(tmp_path: Path) -> None:
    assert run(build(tmp_path, wheel={**WHEEL_FILES, "conftest.py": ""})) == 1


def test_wheel_without_py_typed_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wheel = {k: v for k, v in WHEEL_FILES.items() if k != "pyeconomics/py.typed"}
    assert run(build(tmp_path, wheel=wheel)) == 1
    assert "pyeconomics/py.typed is missing" in capsys.readouterr().err


def test_wheel_version_mismatch_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wheel = {**WHEEL_FILES, f"{INFO}/METADATA": METADATA.replace(VERSION, "9.9.9")}
    assert run(build(tmp_path, wheel=wheel)) == 1
    assert "version '9.9.9'" in capsys.readouterr().err


def test_sdist_with_a_stray_file_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sdist = {**SDIST_FILES, f"{ROOT}/planning/user-context.md": "private"}
    assert run(build(tmp_path, sdist=sdist)) == 1
    assert "planning/user-context.md is not allowlisted" in capsys.readouterr().err


def test_sdist_member_outside_its_root_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(build(tmp_path, sdist={**SDIST_FILES, "stray.txt": ""})) == 1
    assert "stray.txt is outside" in capsys.readouterr().err


def test_modified_pyproject_orig_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sdist = {**SDIST_FILES, f"{ROOT}/pyproject.toml.orig": PYPROJECT + "# edited\n"}
    assert run(build(tmp_path, sdist=sdist)) == 1
    assert "differs from pyproject.toml" in capsys.readouterr().err


def test_sdist_without_pkg_info_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sdist = {k: v for k, v in SDIST_FILES.items() if not k.endswith("PKG-INFO")}
    assert run(build(tmp_path, sdist=sdist)) == 1
    assert "PKG-INFO is missing" in capsys.readouterr().err


def test_sdist_version_mismatch_fails(tmp_path: Path) -> None:
    sdist = {**SDIST_FILES, f"{ROOT}/PKG-INFO": METADATA.replace(VERSION, "9.9.9")}
    assert run(build(tmp_path, sdist=sdist)) == 1


def test_missing_artifact_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = build(tmp_path)
    next((root / "dist").glob("*.whl")).unlink()
    assert run(root) == 1
    assert "expected one wheel and one sdist" in capsys.readouterr().err
