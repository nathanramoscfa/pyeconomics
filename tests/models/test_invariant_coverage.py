# tests/models/test_invariant_coverage.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Every invariant a model declares has a marked property test.

A model's ``spec.invariants`` are its promises (a bond's price falls as its yield
rises). The definition of done (ROADMAP section 5) asks for one property test for
each, so this meta-test finds them. A test names the invariant it holds with
``@pytest.mark.invariant("<model id>", "<invariant id>")`` above a hypothesis
``@given`` test; ``@pytest.mark.oracle("<model id>")`` marks a test that compares
the model with an independent library.

The scan reads the test tree with ``ast`` and imports nothing, so it sees every
marker whatever subset of tests runs, and a marker cannot hide in a module that
fails to import. It fails when:

- a registered model declares an invariant that no ``invariant`` test covers;
- a marker names a model or an invariant that does not exist;
- the marked test is not a hypothesis property test (no ``@given``);
- a marker is not on a test function, or its arguments are not string literals;
- an ``oracle`` test can skip: it carries ``skip``, ``skipif`` or ``xfail``, or its
  module calls ``pytest.importorskip``. A missing oracle library must be an import
  error that fails the suite, never a silent skip.
"""

from __future__ import annotations

import ast
import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
import toy_models as tm

from pyeconomics.core import Invariant, Model, Registry
from pyeconomics.core.registry import installed

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

TESTS_ROOT: Final = Path(__file__).resolve().parents[1]

_SKIPPED_DIRS: Final = {"__pycache__", "fixtures"}
_ARGUMENTS: Final = {"invariant": 2, "oracle": 1}
_SKIPS: Final = {"skip", "skipif", "xfail"}


@dataclass(frozen=True, slots=True)
class Marker:
    """One ``invariant`` or ``oracle`` marker on a test function."""

    kind: str
    model_id: str
    invariant_id: str | None
    where: str
    property_test: bool
    can_skip: bool


def _name(node: ast.expr) -> str | None:
    """The last name of a decorator, call or attribute chain."""
    if isinstance(node, ast.Call):
        return _name(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _marker_kind(call: ast.Call) -> str | None:
    """``invariant`` or ``oracle`` for ``pytest.mark.<kind>(...)``, else ``None``."""
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr not in _ARGUMENTS:
        return None
    base = func.value
    is_mark = (isinstance(base, ast.Attribute) and base.attr == "mark") or (
        isinstance(base, ast.Name) and base.id == "mark"
    )
    return func.attr if is_mark else None


def _scan_file(path: Path, where: str) -> tuple[list[Marker], list[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=where)
    except (SyntaxError, UnicodeDecodeError) as error:
        return [], [f"{where}: cannot be parsed ({error})"]
    markers: list[Marker] = []
    problems: list[str] = []
    placed: set[int] = set()
    skips_on_import = any(
        isinstance(n, ast.Call) and _name(n) == "importorskip" for n in ast.walk(tree)
    )
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        names = [_name(d) for d in node.decorator_list]
        property_test = "given" in names
        can_skip = skips_on_import or any(n in _SKIPS for n in names)
        for decorator in node.decorator_list:
            kind = _marker_kind(decorator) if isinstance(decorator, ast.Call) else None
            if kind is None or not isinstance(decorator, ast.Call):
                continue
            placed.add(id(decorator))
            at = f"{where}:{decorator.lineno}"
            args = [a.value for a in decorator.args if isinstance(a, ast.Constant)]
            literal = len(args) == len(decorator.args) and all(
                isinstance(a, str) for a in args
            )
            if not literal or decorator.keywords or len(args) != _ARGUMENTS[kind]:
                problems.append(
                    f"{at}: {kind} takes {_ARGUMENTS[kind]} string literal(s) as "
                    "positional arguments"
                )
                continue
            markers.append(
                Marker(
                    kind=kind,
                    model_id=str(args[0]),
                    invariant_id=str(args[1]) if kind == "invariant" else None,
                    where=at,
                    property_test=property_test,
                    can_skip=can_skip,
                )
            )
    problems += [
        f"{where}:{node.lineno}: a {_marker_kind(node)} marker must decorate a test "
        "function directly, not a class, a module or a parametrize mark"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _marker_kind(node) is not None
        and id(node) not in placed
    ]
    return markers, problems


def scan(root: Path) -> tuple[list[Marker], list[str]]:
    """Read every ``.py`` file under ``root`` and return its markers and faults."""
    markers: list[Marker] = []
    problems: list[str] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if _SKIPPED_DIRS & set(relative.parts):
            continue
        found, faults = _scan_file(path, relative.as_posix())
        markers += found
        problems += faults
    return markers, problems


def problems_with(
    registry: Registry, markers: Iterable[Marker], scan_problems: Sequence[str] = ()
) -> list[str]:
    """Hold the markers to the registry; return every way they fall short."""
    models = {model.id: model for model in registry.models()}
    problems = list(scan_problems)
    covered: set[tuple[str, str]] = set()
    for marker in markers:
        model = models.get(marker.model_id)
        if model is None:
            problems.append(
                f"{marker.where}: the {marker.kind} marker names unknown model "
                f"{marker.model_id!r}"
            )
        elif marker.kind == "oracle":
            if marker.can_skip:
                problems.append(
                    f"{marker.where}: an oracle test must never skip; remove the "
                    "skip mark or importorskip so a missing library fails the suite"
                )
        elif marker.invariant_id not in {i.id for i in model.spec.invariants}:
            problems.append(
                f"{marker.where}: {marker.model_id!r} declares no invariant "
                f"{marker.invariant_id!r}"
            )
        elif not marker.property_test:
            problems.append(
                f"{marker.where}: the test for {marker.model_id!r} / "
                f"{marker.invariant_id!r} is not a hypothesis property test (@given)"
            )
        else:
            covered.add((marker.model_id, str(marker.invariant_id)))
    problems += [
        f"{model.id}: invariant {invariant.id!r} has no @pytest.mark.invariant "
        "property test"
        for model in models.values()
        for invariant in model.spec.invariants
        if (model.id, invariant.id) not in covered
    ]
    return problems


def test_every_declared_invariant_has_a_marked_property_test() -> None:
    markers, scan_problems = scan(TESTS_ROOT)
    problems = problems_with(installed(), markers, scan_problems)
    assert not problems, "\n".join(problems)


# --- the meta-test holds itself to account: toy models and written test files ------

ZERO = "fixed_income.toy_zero_coupon"
INVARIANT = "price_falls_as_yield_rises"

COVERED = f"""
import pytest
from hypothesis import given, strategies as st


@pytest.mark.invariant("{ZERO}", "{INVARIANT}")
@given(st.floats())
def test_price_falls(x):
    pass
"""


def run(
    tmp_path: Path, files: dict[str, str], registry: Registry | None = None
) -> list[str]:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    markers, faults = scan(tmp_path)
    return problems_with(registry or tm.toy_registry(tm.zero_coupon), markers, faults)


def test_a_covered_invariant_passes(tmp_path: Path) -> None:
    assert run(tmp_path, {"test_a.py": COVERED}) == []


def test_an_invariant_with_no_marked_test_fails(tmp_path: Path) -> None:
    found = run(tmp_path, {"test_a.py": "def test_nothing():\n    pass\n"})
    assert found == [
        f"{ZERO}: invariant '{INVARIANT}' has no @pytest.mark.invariant property test"
    ]


def test_the_marker_may_sit_in_any_file_under_the_tree(tmp_path: Path) -> None:
    assert run(tmp_path, {"models/risk/test_deep.py": COVERED}) == []


def test_a_marker_naming_an_unknown_model_fails(tmp_path: Path) -> None:
    text = COVERED.replace(ZERO, "fixed_income.nowhere")
    found = run(tmp_path, {"test_a.py": text})
    assert any("unknown model 'fixed_income.nowhere'" in f for f in found)
    assert any("has no @pytest.mark.invariant" in f for f in found)


def test_a_marker_naming_an_unknown_invariant_fails(tmp_path: Path) -> None:
    text = COVERED.replace(INVARIANT, "not_declared")
    found = run(tmp_path, {"test_a.py": text})
    assert any("declares no invariant 'not_declared'" in f for f in found)


def test_a_marked_test_that_is_not_a_property_test_fails(tmp_path: Path) -> None:
    text = COVERED.replace("@given(st.floats())\n", "")
    found = run(tmp_path, {"test_a.py": text})
    assert any("not a hypothesis property test" in f for f in found)
    assert any("has no @pytest.mark.invariant" in f for f in found)


def test_the_given_decorator_may_be_spelled_either_way(tmp_path: Path) -> None:
    text = COVERED.replace("@given(st.floats())", "@hypothesis.given(st.floats())")
    assert run(tmp_path, {"test_a.py": text}) == []


def test_the_mark_may_be_imported_by_name(tmp_path: Path) -> None:
    text = COVERED.replace("@pytest.mark.invariant", "@mark.invariant").replace(
        "import pytest", "from pytest import mark"
    )
    assert run(tmp_path, {"test_a.py": text}) == []


@pytest.mark.parametrize(
    "text",
    [
        '@pytest.mark.invariant("a.b", "c")\nclass TestIt:\n    pass\n',
        'pytestmark = pytest.mark.invariant("a.b", "c")\n',
        (
            "@pytest.mark.parametrize(\n"
            '    "x", [pytest.param(1, marks=pytest.mark.oracle("a.b"))]\n'
            ")\n"
            "def test_it(x):\n    pass\n"
        ),
    ],
    ids=["class", "module", "parametrize"],
)
def test_a_marker_must_decorate_a_function_directly(tmp_path: Path, text: str) -> None:
    found = run(tmp_path, {"test_a.py": "import pytest\n" + text})
    assert any("must decorate a test function directly" in f for f in found)


@pytest.mark.parametrize(
    "marker",
    [
        '@pytest.mark.invariant("a.b")',
        '@pytest.mark.invariant("a.b", "c", "d")',
        "@pytest.mark.invariant(MODEL, INVARIANT)",
        '@pytest.mark.invariant("a.b", 3)',
        '@pytest.mark.invariant("a.b", invariant_id="c")',
        "@pytest.mark.oracle()",
        '@pytest.mark.oracle("a.b", "statsmodels")',
    ],
)
def test_marker_arguments_must_be_string_literals_of_the_right_count(
    tmp_path: Path, marker: str
) -> None:
    text = f"import pytest\n\n{marker}\ndef test_it():\n    pass\n"
    found = run(tmp_path, {"test_a.py": text})
    assert any("string literal(s) as positional arguments" in f for f in found)


def test_one_test_may_hold_several_invariants(tmp_path: Path) -> None:
    spec = dataclasses.replace(
        tm.zero_coupon.spec,
        invariants=(
            Invariant(id="first", statement="One."),
            Invariant(id="second", statement="Two."),
        ),
    )
    registry = Registry.from_models(Model(spec, tm.zero_coupon.compute))
    text = (
        "import pytest\nfrom hypothesis import given\n\n"
        f'@pytest.mark.invariant("{ZERO}", "first")\n'
        f'@pytest.mark.invariant("{ZERO}", "second")\n'
        "@given(1)\ndef test_both(x):\n    pass\n"
    )
    assert run(tmp_path, {"test_a.py": text}, registry) == []
    one = text.replace('"second"', '"first"')
    found = run(tmp_path, {"test_a.py": one}, registry)
    assert found == [
        f"{ZERO}: invariant 'second' has no @pytest.mark.invariant property test"
    ]


def test_a_model_with_no_invariants_needs_no_marker(tmp_path: Path) -> None:
    registry = Registry.from_models(tm.time_value)
    assert run(tmp_path, {}, registry) == []


# --- oracle tests never skip -------------------------------------------------------

ORACLE = f"""
import pytest


@pytest.mark.oracle("{ZERO}")
def test_against_quantlib():
    import QuantLib
"""


def test_an_oracle_test_that_can_fail_is_fine(tmp_path: Path) -> None:
    assert run(tmp_path, {"test_o.py": ORACLE, "test_a.py": COVERED}) == []


def test_an_oracle_marker_naming_an_unknown_model_fails(tmp_path: Path) -> None:
    text = ORACLE.replace(ZERO, "fixed_income.nowhere")
    found = run(tmp_path, {"test_o.py": text, "test_a.py": COVERED})
    assert any("oracle marker names unknown model" in f for f in found)


@pytest.mark.parametrize(
    "skip",
    [
        "@pytest.mark.skip",
        '@pytest.mark.skipif(True, reason="x")',
        "@pytest.mark.xfail",
    ],
)
def test_an_oracle_test_that_can_skip_fails(tmp_path: Path, skip: str) -> None:
    text = ORACLE.replace("@pytest.mark.oracle", f"{skip}\n@pytest.mark.oracle")
    found = run(tmp_path, {"test_o.py": text, "test_a.py": COVERED})
    assert any("must never skip" in f for f in found)


def test_an_oracle_module_that_uses_importorskip_fails(tmp_path: Path) -> None:
    text = ORACLE.replace(
        "    import QuantLib", '    quantlib = pytest.importorskip("QuantLib")'
    )
    found = run(tmp_path, {"test_o.py": text, "test_a.py": COVERED})
    assert any("must never skip" in f for f in found)


# --- the scan itself -----------------------------------------------------------------


def test_a_file_that_cannot_be_parsed_is_reported(tmp_path: Path) -> None:
    found = run(tmp_path, {"test_a.py": COVERED, "test_broken.py": "def (:\n"})
    assert any("test_broken.py: cannot be parsed" in f for f in found)


def test_fixture_and_cache_directories_are_not_scanned(tmp_path: Path) -> None:
    hidden = COVERED.replace(INVARIANT, "not_declared")
    files = {
        "test_a.py": COVERED,
        "fixtures/legacy/test_x.py": hidden,
        "__pycache__/test_y.py": hidden,
    }
    assert run(tmp_path, files) == []


def test_an_empty_tree_and_an_empty_registry_agree(tmp_path: Path) -> None:
    assert run(tmp_path, {}, Registry.from_models()) == []
