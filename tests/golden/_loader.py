# tests/golden/_loader.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Golden-case files: their format, loader and the rules a model is held to.

A golden file holds the handful of published values one model must reproduce
(tests/golden/README.md fixes the format). This module parses a file with
``tomllib`` only, so no fixture content is ever evaluated, rejects unknown keys,
and checks the rules of ROADMAP section 5 "Model quality and governance":

- every registered model has a golden file, and every file names a registered
  model and sits where its id puts it;
- every case cites a defined source with a locator (an identity needs none);
- at least three cases and an edge case, unless the file records why not;
- a textbook value is recomputed independently or quoted at its published
  precision, with a tolerance no tighter than that precision;
- an expected field is an output of the case's calculation, and the model's
  outputs match within the tolerance (the case's own, else ADR-0008's default).

:func:`audit` runs the static rules over a directory of files; :func:`run_case`
runs one case. The tests of the harness itself (``test_harness.py``) give each
rule a toy model and a file that breaks it.
"""

from __future__ import annotations

import datetime as dt
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Final, TypeGuard, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pyeconomics.core import (
    EXACT,
    InputError,
    Tolerance,
    Unit,
    default_tolerance,
    run_model,
)
from pyeconomics.core.spec import CALCULATION_FIELD, union_members

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from pyeconomics.core import Model, Registry
    from pyeconomics.core.results import Result

__all__ = [
    "GOLDEN_ROOT",
    "MIN_CASES",
    "SOURCE_KINDS",
    "Audit",
    "Case",
    "GoldenError",
    "GoldenFile",
    "Source",
    "audit",
    "golden_path",
    "load_golden",
    "parse_golden",
    "run_case",
]

#: The directory the golden files live under: ``<domain>/<name>.toml``.
GOLDEN_ROOT: Final = Path(__file__).resolve().parent

#: The kinds of source a case may cite (the Citation rule in the Phase 2 roadmap).
SOURCE_KINDS: Final = ("certified", "official", "paper", "textbook", "identity")

#: Fewer cases than this need a ``min_cases_reason``.
MIN_CASES: Final = 3

#: A string that starts with this is a scaffold's placeholder, not a value.
PLACEHOLDER: Final = "TODO"

_SOURCE_REQUIRED: Final = {"key", "kind", "citation"}
_SOURCE_OPTIONAL: Final = {
    "url",
    "doi",
    "isbn",
    "recomputed_with",
    "published_digits",
}
_CASE_REQUIRED: Final = {"id", "source", "edge", "inputs"}
_CASE_OPTIONAL: Final = {
    "locator",
    "expected",
    "expected_none",
    "tolerance",
    "note",
}
_TOLERANCE_KEYS: Final = {"abs", "rel"}

#: Slack for comparing a tolerance with half a unit of published precision.
_HALF_UNIT_SLACK: Final = 1e-9


class GoldenError(ValueError):
    """A golden file that cannot be read as the format asks.

    Attributes
    ----------
    problems
        Every fault found, each naming the file and the key.
    """

    def __init__(self, problems: Sequence[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = tuple(problems)


@dataclass(frozen=True, slots=True)
class Source:
    """A source one or more cases cite."""

    key: str
    kind: str
    citation: str
    url: str | None = None
    doi: str | None = None
    isbn: str | None = None
    recomputed_with: str | None = None
    published_digits: int | None = None


@dataclass(frozen=True, slots=True)
class Case:
    """One golden case: inputs, expected outputs and where the values come from."""

    id: str
    source: str
    edge: bool
    inputs: Mapping[str, object]
    locator: str | None = None
    expected: Mapping[str, object] | None = None
    expected_none: tuple[str, ...] = ()
    tolerance: Mapping[str, Tolerance] | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class GoldenFile:
    """A parsed golden file."""

    path: Path
    model: str
    sources: tuple[Source, ...]
    cases: tuple[Case, ...]
    min_cases_reason: str | None = None

    def source(self, key: str) -> Source | None:
        """Return the source with this key, or ``None``."""
        return next((s for s in self.sources if s.key == key), None)


# --- parsing ----------------------------------------------------------------------


class _Reader:
    """Reads one table, collecting every fault instead of stopping at the first."""

    def __init__(self, where: str, problems: list[str]) -> None:
        self.where = where
        self.problems = problems

    def fault(self, detail: str) -> None:
        self.problems.append(f"{self.where}: {detail}")

    def keys(
        self, table: Mapping[str, object], required: set[str], optional: set[str]
    ) -> None:
        for key in sorted(set(table) - required - optional):
            self.fault(f"unknown key {key!r}")
        for key in sorted(required - set(table)):
            self.fault(f"missing key {key!r}")

    def text(self, table: Mapping[str, object], key: str) -> str | None:
        value = table.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            self.fault(f"{key!r} must be a non-empty string")
            return None
        return value

    def boolean(self, table: Mapping[str, object], key: str) -> bool:
        value = table.get(key)
        if not isinstance(value, bool):
            if key in table:
                self.fault(f"{key!r} must be true or false")
            return False
        return value


def _is_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _tables(
    data: Mapping[str, object], key: str, where: str, problems: list[str]
) -> list[Mapping[str, object]]:
    raw = data.get(key, [])
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        problems.append(f"{where}: {key!r} must be an array of tables ([[{key}]])")
        return []
    return list(raw)


def _parse_source(
    table: Mapping[str, object], where: str, problems: list[str]
) -> Source:
    reader = _Reader(where, problems)
    reader.keys(table, _SOURCE_REQUIRED, _SOURCE_OPTIONAL)
    kind = reader.text(table, "kind") or ""
    if kind and kind not in SOURCE_KINDS:
        reader.fault(f"kind {kind!r} is not one of {', '.join(SOURCE_KINDS)}")
    digits = table.get("published_digits")
    if digits is not None and (
        not isinstance(digits, int) or isinstance(digits, bool) or digits < 0
    ):
        reader.fault("'published_digits' must be a whole number of decimal places")
        digits = None
    return Source(
        key=reader.text(table, "key") or "",
        kind=kind,
        citation=reader.text(table, "citation") or "",
        url=reader.text(table, "url"),
        doi=reader.text(table, "doi"),
        isbn=reader.text(table, "isbn"),
        recomputed_with=reader.text(table, "recomputed_with"),
        published_digits=digits,
    )


def _parse_tolerance(raw: object, reader: _Reader) -> dict[str, Tolerance] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        reader.fault("'tolerance' must be a table of output field -> {abs, rel}")
        return None
    parsed: dict[str, Tolerance] = {}
    for name, entry in raw.items():
        if not isinstance(entry, dict) or not entry:
            reader.fault(f"tolerance.{name} must be a table with 'abs' and/or 'rel'")
            continue
        for key in sorted(set(entry) - _TOLERANCE_KEYS):
            reader.fault(f"tolerance.{name}: unknown key {key!r}")
        values = {k: entry.get(k, 0.0) for k in _TOLERANCE_KEYS}
        if not all(_is_number(v) for v in values.values()):
            reader.fault(f"tolerance.{name}: 'abs' and 'rel' must be numbers")
            continue
        try:
            parsed[name] = Tolerance(
                abs_tol=float(values["abs"]), rel_tol=float(values["rel"])
            )
        except ValueError as error:
            reader.fault(f"tolerance.{name}: {error}")
    return parsed


def _parse_case(table: Mapping[str, object], where: str, problems: list[str]) -> Case:
    name = table.get("id")
    reader = _Reader(f"{where} ({name})" if isinstance(name, str) else where, problems)
    reader.keys(table, _CASE_REQUIRED, _CASE_OPTIONAL)
    inputs = table.get("inputs", {})
    if not isinstance(inputs, dict):
        reader.fault("'inputs' must be a table")
        inputs = {}
    expected = table.get("expected")
    if expected is not None and not isinstance(expected, dict):
        reader.fault("'expected' must be a table of output field -> value")
        expected = None
    none_fields = table.get("expected_none", [])
    if not isinstance(none_fields, list) or not all(
        isinstance(item, str) for item in none_fields
    ):
        reader.fault("'expected_none' must be a list of output field names")
        none_fields = []
    if not expected and not none_fields:
        reader.fault("a case needs 'expected' values or an 'expected_none' list")
    return Case(
        id=reader.text(table, "id") or "",
        source=reader.text(table, "source") or "",
        edge=reader.boolean(table, "edge"),
        inputs=inputs,
        locator=reader.text(table, "locator"),
        expected=expected,
        expected_none=tuple(none_fields),
        tolerance=_parse_tolerance(table.get("tolerance"), reader),
        note=reader.text(table, "note"),
    )


def parse_golden(data: Mapping[str, object], path: Path) -> GoldenFile:
    """Build a :class:`GoldenFile` from parsed TOML.

    Raises
    ------
    GoldenError
        Listing every unknown key, missing key and wrongly typed value.
    """
    problems: list[str] = []
    top = _Reader(path.name, problems)
    top.keys(data, {"model", "sources", "cases"}, {"min_cases_reason"})
    model = top.text(data, "model") or ""
    reason = top.text(data, "min_cases_reason")
    sources = tuple(
        _parse_source(table, f"{path.name}: sources[{index}]", problems)
        for index, table in enumerate(_tables(data, "sources", path.name, problems))
    )
    cases = tuple(
        _parse_case(table, f"{path.name}: cases[{index}]", problems)
        for index, table in enumerate(_tables(data, "cases", path.name, problems))
    )
    if problems:
        raise GoldenError(problems)
    return GoldenFile(
        path=path, model=model, sources=sources, cases=cases, min_cases_reason=reason
    )


def load_golden(path: Path) -> GoldenFile:
    """Read a golden file with ``tomllib``; nothing in it is ever evaluated.

    Raises
    ------
    GoldenError
        If the file is not valid TOML or does not follow the format.
    """
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise GoldenError([f"{path.name}: not valid TOML: {error}"]) from error
    return parse_golden(data, path)


# --- locating files ------------------------------------------------------------


def golden_path(model_id: str, root: Path = GOLDEN_ROOT) -> Path:
    """Return where a model's golden file lives.

    ``fixed_income.duration`` is ``<root>/fixed_income/duration.toml``. An id with a
    family, ``domain.family.name``, joins the last two parts:
    ``<root>/domain/family_name.toml``.
    """
    domain, _, rest = model_id.partition(".")
    return root / domain / f"{rest.replace('.', '_')}.toml"


# --- what a case expects --------------------------------------------------------


def output_class(
    model: Model[Any, Any], inputs: Mapping[str, object]
) -> type[BaseModel]:
    """Return the output model a case's inputs select.

    A model with one output class returns it. A model with several calculations
    returns the member whose ``calculation`` matches the inputs'.

    Raises
    ------
    ValueError
        If the model has several calculations and the inputs name none of them.
    """
    members = _model_classes(model.spec.outputs)
    if len(members) == 1:
        return members[0]
    wanted = inputs.get(CALCULATION_FIELD)
    for member in members:
        field = member.model_fields.get(CALCULATION_FIELD)
        if field is not None and field.default == wanted:
            return member
    names = ", ".join(
        sorted(
            str(m.model_fields[CALCULATION_FIELD].default)
            for m in members
            if CALCULATION_FIELD in m.model_fields
        )
    )
    msg = f"the inputs need a 'calculation' naming one of: {names}"
    raise ValueError(msg)


def _model_classes(annotation: object) -> list[type[BaseModel]]:
    """Return the model classes of a model, or of the members of its union."""
    return [
        member
        for member in union_members(annotation)
        if isinstance(member, type) and issubclass(member, BaseModel)
    ]


def _unit_in(items: Iterable[object]) -> Unit | None:
    """Find a unit marker among annotation metadata, looking inside ``Field(...)``."""
    found: Unit | None = None
    for item in items:
        if isinstance(item, Unit):
            found = item
        elif isinstance(item, FieldInfo):
            found = _unit_in(item.metadata) or found
    return found


def _unit_of(annotation: object, metadata: Iterable[object] = ()) -> Unit | None:
    """Find the unit marker of a field, looking into array elements and options."""
    found = _unit_in(metadata)
    while get_origin(annotation) is Annotated:
        args = get_args(annotation)
        annotation = args[0]
        found = _unit_in(args[1:]) or found
    if found is not None:
        return found
    for arg in get_args(annotation):
        if arg is not Ellipsis and arg is not type(None):
            found = _unit_of(arg) or found
    return found


def field_tolerance(cls: type[BaseModel], name: str) -> Tolerance:
    """Return ADR-0008's default tolerance for an output field (exact if unitless)."""
    info = cls.model_fields[name]
    unit = _unit_of(info.annotation, info.metadata)
    return default_tolerance(unit.kind) if unit is not None else EXACT


def case_tolerance(cls: type[BaseModel], case: Case, name: str) -> Tolerance:
    """Return the tolerance a case applies to one output: its own, else the default."""
    if case.tolerance is not None and name in case.tolerance:
        return case.tolerance[name]
    return field_tolerance(cls, name)


def _numbers(value: object) -> list[float]:
    """Return the numbers in an expected value, a list's items included."""
    if isinstance(value, list | tuple):
        return [n for item in value for n in _numbers(item)]
    return [float(value)] if _is_number(value) else []


# --- static rules ---------------------------------------------------------------


def _source_problems(golden: GoldenFile) -> list[str]:
    name = golden.path.name
    problems: list[str] = []
    seen: set[str] = set()
    for source in golden.sources:
        if source.key in seen:
            problems.append(f"{name}: source {source.key!r} is defined twice")
        seen.add(source.key)
        where = f"{name}: source {source.key!r}"
        if source.kind != "identity" and not (source.url or source.doi or source.isbn):
            problems.append(f"{where} needs a url, doi or isbn")
        if source.kind == "textbook" and not (
            source.recomputed_with or source.published_digits is not None
        ):
            problems.append(
                f"{where} is a textbook value: give 'recomputed_with' (the "
                "independent method) or 'published_digits'"
            )
    return problems


def _case_problems(golden: GoldenFile, model: Model[Any, Any] | None) -> list[str]:
    name = golden.path.name
    problems: list[str] = []
    seen: set[str] = set()
    for case in golden.cases:
        where = f"{name}: case {case.id!r}"
        if case.id in seen:
            problems.append(f"{where} is defined twice")
        seen.add(case.id)
        source = golden.source(case.source)
        if source is None:
            problems.append(f"{where} cites the undefined source {case.source!r}")
            continue
        if source.kind != "identity" and not case.locator:
            problems.append(
                f"{where} has no locator (page, table, section or equation) in "
                f"{case.source!r}"
            )
        if model is not None:
            problems += _output_problems(model, case, source, where)
    return problems


def _output_problems(
    model: Model[Any, Any],
    case: Case,
    source: Source,
    where: str,
) -> list[str]:
    try:
        cls = output_class(model, case.inputs)
    except ValueError as error:
        return [f"{where}: {error}"]
    named = [*(case.expected or {}), *case.expected_none, *(case.tolerance or {})]
    unknown = sorted({field for field in named if field not in cls.model_fields})
    if unknown:
        return [
            (
                f"{where}: {', '.join(unknown)} is not an output of "
                f"{cls.__name__} (outputs: {', '.join(cls.model_fields)})"
            )
        ]
    problems: list[str] = []
    both = sorted(set(case.expected or {}) & set(case.expected_none))
    if both:
        problems.append(
            f"{where}: {', '.join(both)} is both expected and expected_none"
        )
    if (
        source.kind == "textbook"
        and not source.recomputed_with
        and source.published_digits is not None
    ):
        problems += _precision_problems(cls, case, source.published_digits, where)
    return problems


def _precision_problems(
    cls: type[BaseModel], case: Case, digits: int, where: str
) -> list[str]:
    """Hold a textbook case's tolerance to half a unit of the published digits."""
    half_unit = 0.5 * 10.0**-digits
    problems = []
    for name, value in (case.expected or {}).items():
        tolerance = case_tolerance(cls, case, name)
        for number in _numbers(value):
            effective = max(tolerance.rel_tol * abs(number), tolerance.abs_tol)
            if effective < half_unit * (1 - _HALF_UNIT_SLACK):
                problems.append(
                    f"{where}: {name} = {number} is published to {digits} decimal "
                    f"places, so its tolerance must be at least {half_unit:g}, not "
                    f"{effective:g}; loosen it, or recompute the value with a named "
                    "independent method ('recomputed_with')"
                )
                break
    return problems


def _placeholders(golden: GoldenFile) -> list[str]:
    """Find scaffold placeholders left in the file."""
    texts: list[tuple[str, str]] = [("min_cases_reason", golden.min_cases_reason or "")]
    for source in golden.sources:
        texts += [
            (f"source {source.key!r} {label}", value or "")
            for label, value in (
                ("citation", source.citation),
                ("url", source.url),
                ("recomputed_with", source.recomputed_with),
            )
        ]
    for case in golden.cases:
        texts += [
            (f"case {case.id!r} locator", case.locator or ""),
            (f"case {case.id!r} id", case.id),
        ]
        texts += [
            (f"case {case.id!r} {k}", v)
            for k, v in case.inputs.items()
            if isinstance(v, str)
        ]
    return [
        f"{golden.path.name}: {label} is still a placeholder ({value!r})"
        for label, value in texts
        if value.startswith(PLACEHOLDER)
    ]


def file_problems(golden: GoldenFile, model: Model[Any, Any] | None) -> list[str]:
    """Return every static rule the file breaks; ``model`` is its registered model.

    With no model the rules that need its outputs are skipped (the registry
    check reports the missing model).
    """
    name = golden.path.name
    problems = _placeholders(golden)
    problems += _source_problems(golden)
    problems += _case_problems(golden, model)
    if len(golden.cases) < MIN_CASES and not golden.min_cases_reason:
        problems.append(
            f"{name}: {len(golden.cases)} case(s); the definition of done needs "
            f"at least {MIN_CASES}, or a 'min_cases_reason' saying why not"
        )
    if not any(case.edge for case in golden.cases) and not golden.min_cases_reason:
        problems.append(
            f"{name}: no case has edge = true; add one (zero or negative rates, a "
            "maturity of 50 years or more, a volatility of 2.0 or more, or a "
            "degenerate input) or record a 'min_cases_reason'"
        )
    return problems


# --- the audit ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Audit:
    """The result of auditing a directory of golden files against a registry."""

    files: tuple[GoldenFile, ...]
    problems: tuple[str, ...]


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def audit(registry: Registry, root: Path = GOLDEN_ROOT) -> Audit:
    """Check every golden file under ``root`` against the registry's models.

    Reports a registered model with no file, a file naming an unregistered
    model, two files for one model, a file in the wrong place, and every
    problem :func:`file_problems` finds.
    """
    problems: list[str] = []
    files: list[GoldenFile] = []
    by_model: dict[str, list[GoldenFile]] = {}
    for path in sorted(root.rglob("*.toml")):
        relative = path.relative_to(root).as_posix()
        try:
            golden = load_golden(path)
        except GoldenError as error:
            problems += [f"{relative}: {p}" for p in error.problems]
            continue
        files.append(golden)
        by_model.setdefault(golden.model, []).append(golden)
    registered = {model.id: model for model in registry.models()}
    for model_id in sorted(by_model):
        group = by_model[model_id]
        if model_id not in registered:
            problems.append(
                f"{', '.join(g.path.relative_to(root).as_posix() for g in group)}: "
                f"names {model_id!r}, which is not a registered model"
            )
        if len(group) > 1:
            names = ", ".join(g.path.relative_to(root).as_posix() for g in group)
            problems.append(f"{model_id}: more than one golden file ({names})")
        for golden in group:
            placed = golden_path(model_id, root)
            if golden.path != placed and model_id in registered:
                problems.append(
                    f"{golden.path.relative_to(root).as_posix()}: {model_id!r} "
                    f"belongs in {_relative(placed, root)}"
                )
            problems += file_problems(golden, registered.get(model_id))
    for model_id in sorted(registered):
        if model_id not in by_model:
            where = _relative(golden_path(model_id, root), root)
            problems.append(f"{model_id}: no golden file (expected {where})")
    return Audit(tuple(files), tuple(problems))


# --- running a case ---------------------------------------------------------------


def _agrees(actual: object, expected: object, tolerance: Tolerance) -> bool:
    """Whether an output agrees with its expected value (lists item by item)."""
    if isinstance(expected, list | tuple):
        return (
            isinstance(actual, list | tuple)
            and len(actual) == len(expected)
            and all(
                _agrees(a, e, tolerance) for a, e in zip(actual, expected, strict=True)
            )
        )
    if isinstance(expected, bool) or isinstance(actual, bool):
        return actual is expected
    if isinstance(expected, str) or isinstance(actual, str):
        return bool(actual == expected)
    if isinstance(expected, dt.date) or isinstance(actual, dt.date):
        return bool(actual == expected)
    if not (_is_number(actual) and _is_number(expected)):
        return False
    return tolerance.isclose(float(actual), float(expected))


def _run_directly(
    model: Model[Any, Any], inputs: Mapping[str, object]
) -> Result[Any, Any]:
    return run_model(model, inputs)


def run_case(
    model: Model[Any, Any],
    case: Case,
    runner: Callable[
        [Model[Any, Any], Mapping[str, object]], Result[Any, Any]
    ] = _run_directly,
) -> list[str]:
    """Run one case and return how its outputs differ from the expected values.

    Parameters
    ----------
    model
        The model the case belongs to.
    case
        The case to run.
    runner
        Runs the model on the inputs; by default :func:`run_model`, and the
        real harness passes ``pyeconomics.run`` by id.

    Returns
    -------
    list of str
        One line per output that disagrees, or that is not an output of the
        case's calculation; empty when the case passes. An input the model
        rejects is a mismatch too.
    """
    try:
        result = runner(model, dict(case.inputs))
    except InputError as error:
        return [f"{case.id}: the model rejected the inputs: {error}"]
    try:
        cls = output_class(model, case.inputs)
    except ValueError as error:
        return [f"{case.id}: {error}"]
    outputs = result.outputs.model_dump(mode="python")
    mismatches: list[str] = []
    for name, expected in (case.expected or {}).items():
        if name not in outputs:
            mismatches.append(f"{case.id}: {name} is not an output of {cls.__name__}")
            continue
        tolerance = case_tolerance(cls, case, name)
        if not _agrees(outputs[name], expected, tolerance):
            mismatches.append(
                f"{case.id}: {name} expected {expected!r}, got {outputs[name]!r} "
                f"(abs_tol {tolerance.abs_tol:g}, rel_tol {tolerance.rel_tol:g})"
            )
    for name in case.expected_none:
        if name not in outputs:
            mismatches.append(f"{case.id}: {name} is not an output of {cls.__name__}")
        elif outputs[name] is not None:
            mismatches.append(f"{case.id}: {name} expected None, got {outputs[name]!r}")
    return mismatches
