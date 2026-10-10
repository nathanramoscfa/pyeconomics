# tests/golden/test_harness.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The golden harness holds its own rules: each one has a file that breaks it.

No catalog model exists yet, so these tests run the harness over toy models and
golden files written to ``tmp_path``. A rule that never failed here would let a
real model through unchecked.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import tomllib
from typing import TYPE_CHECKING, Any

import pytest
import toy_models as tm
import toy_results_models as rm
from _loader import (
    GOLDEN_ROOT,
    Case,
    GoldenError,
    audit,
    file_problems,
    golden_path,
    load_golden,
    parse_golden,
    run_case,
)
from pydantic import Field

from pyeconomics.core import (
    Model,
    ModelInputs,
    ModelOutputs,
    ModelSpec,
    Ratio,
    Registry,
    run_model,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from pyeconomics.core.results import Result

ZERO = "fixed_income.toy_zero_coupon"
ZERO_PATH = "fixed_income/toy_zero_coupon.toml"


def value(item: object) -> str:
    """Write a Python value as a TOML value."""
    if isinstance(item, bool):
        return "true" if item else "false"
    if isinstance(item, dt.date):
        return item.isoformat()
    if isinstance(item, str):
        return json.dumps(item)
    if isinstance(item, list | tuple):
        return "[" + ", ".join(value(i) for i in item) + "]"
    if isinstance(item, dict):
        return "{ " + ", ".join(f"{k} = {value(v)}" for k, v in item.items()) + " }"
    return repr(item)


def case(  # noqa: PLR0913 - one argument per key of a case
    case_id: str,
    source: str,
    inputs: Mapping[str, object],
    expected: Mapping[str, object] | None = None,
    *,
    edge: bool = False,
    locator: str | None = "Part I",
    extra: str = "",
) -> str:
    lines = ["[[cases]]", f"id = {value(case_id)}", f"source = {value(source)}"]
    if locator is not None:
        lines.append(f"locator = {value(locator)}")
    lines += [f"edge = {value(edge)}", f"inputs = {value(dict(inputs))}"]
    if expected is not None:
        lines.append(f"expected = {value(dict(expected))}")
    return "\n".join([*lines, extra, ""])


def price(rate: float, years: float) -> float:
    return float(100 / (1 + rate) ** years)


def at(rate: float, years: float, **kwargs: object) -> dict[str, Any]:
    """Keyword arguments of :func:`case` for a zero-coupon price."""
    inputs = {"face_value": 100, "rate": rate, "years": years}
    return {"inputs": inputs, "expected": {"price": price(rate, years)}, **kwargs}


PAPER = """[[sources]]
key = "paper"
kind = "paper"
citation = "Fisher, I. (1930). The Theory of Interest. Macmillan."
doi = "10.1000/toy"
"""
IDENTITY = """[[sources]]
key = "identity"
kind = "identity"
citation = "The closed form P = F / (1 + y)^T."
"""

GOOD_CASES = (
    case("ten_years", "paper", **at(0.05, 10)),
    case("zero_rate", "identity", **at(0.0, 10), edge=True, locator=None),
    case("negative_rate", "paper", **at(-0.01, 30), edge=True),
)


def file_text(
    cases: Sequence[str] = GOOD_CASES,
    sources: str = PAPER + IDENTITY,
    model: str = ZERO,
    top: str = "",
) -> str:
    return f"model = {value(model)}\n{top}\n{sources}\n{''.join(cases)}"


def problems_of(
    tmp_path: Path,
    text: str,
    model: Model[Any, Any] = tm.zero_coupon,
    relative: str = ZERO_PATH,
) -> list[str]:
    """Write a golden file under ``tmp_path`` and audit it against one model."""
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return list(audit(tm.toy_registry(model), tmp_path).problems)


def assert_problem(problems: Sequence[str], *needles: str) -> None:
    joined = "\n".join(problems)
    assert problems, "the harness accepted a file that breaks a rule"
    for needle in needles:
        assert needle in joined, f"{needle!r} not in:\n{joined}"


# --- a sound file passes ------------------------------------------------------


def test_a_sound_file_passes_every_rule(tmp_path: Path) -> None:
    assert problems_of(tmp_path, file_text()) == []


def test_every_case_of_a_sound_file_runs_within_tolerance(tmp_path: Path) -> None:
    problems_of(tmp_path, file_text())
    golden = load_golden(tmp_path / ZERO_PATH)
    assert [run_case(tm.zero_coupon, c) for c in golden.cases] == [[], [], []]


def test_the_empty_registry_and_the_empty_directory_agree(tmp_path: Path) -> None:
    assert audit(Registry.from_models(), tmp_path).problems == ()


# --- finding the files --------------------------------------------------------


def test_a_registered_model_without_a_golden_file_fails(tmp_path: Path) -> None:
    result = audit(tm.toy_registry(tm.zero_coupon), tmp_path)
    assert_problem(result.problems, ZERO, "no golden file", ZERO_PATH)


def test_a_file_naming_an_unregistered_model_fails(tmp_path: Path) -> None:
    text = file_text(model="fixed_income.not_a_model")
    path = tmp_path / "fixed_income" / "not_a_model.toml"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    result = audit(Registry.from_models(), tmp_path)
    assert_problem(
        result.problems, "fixed_income.not_a_model", "not a registered model"
    )


def test_two_files_for_one_model_fail(tmp_path: Path) -> None:
    problems_of(tmp_path, file_text())
    other = tmp_path / "fixed_income" / "copy.toml"
    other.write_text(file_text(), encoding="utf-8")
    result = audit(tm.toy_registry(tm.zero_coupon), tmp_path)
    assert_problem(result.problems, "more than one golden file", "copy.toml")


def test_a_file_in_the_wrong_place_fails(tmp_path: Path) -> None:
    found = problems_of(tmp_path, file_text(), relative="elsewhere/zero.toml")
    assert_problem(found, "belongs in", ZERO_PATH)


@pytest.mark.parametrize(
    ("model_id", "relative"),
    [
        ("fixed_income.duration", "fixed_income/duration.toml"),
        ("equity.dcf.gordon_growth", "equity/dcf_gordon_growth.toml"),
    ],
)
def test_the_path_follows_the_id(tmp_path: Path, model_id: str, relative: str) -> None:
    assert golden_path(model_id, tmp_path) == tmp_path / relative


# --- the format ---------------------------------------------------------------


def test_a_file_that_is_not_toml_fails(tmp_path: Path) -> None:
    assert_problem(problems_of(tmp_path, "model = = 1"), "not valid TOML")


@pytest.mark.parametrize(
    ("text", "needle"),
    [
        (file_text(top='extra = "x"'), "unknown key 'extra'"),
        (
            file_text(
                sources=PAPER.replace("[[sources]]", '[[sources]]\nnote = "x"')
                + IDENTITY
            ),
            "unknown key 'note'",
        ),
        (
            file_text(
                cases=[
                    GOOD_CASES[0].replace(
                        "edge = false", 'edge = false\ncolour = "red"'
                    ),
                    *GOOD_CASES[1:],
                ]
            ),
            "unknown key 'colour'",
        ),
        (
            file_text(
                cases=[
                    GOOD_CASES[0]
                    + "tolerance = { price = { abs = 1.0, digits = 2 } }\n",
                    *GOOD_CASES[1:],
                ]
            ),
            "unknown key 'digits'",
        ),
        (
            file_text(
                sources=PAPER.replace('kind = "paper"', 'kind = "blog"') + IDENTITY
            ),
            "kind 'blog'",
        ),
        (
            file_text(
                cases=[
                    GOOD_CASES[0].replace("edge = false", 'edge = "no"'),
                    *GOOD_CASES[1:],
                ]
            ),
            "'edge' must be true or false",
        ),
        (
            file_text(
                cases=[
                    GOOD_CASES[0].replace("inputs = ", "inputs = 5 #"),
                    *GOOD_CASES[1:],
                ]
            ),
            "'inputs' must be a table",
        ),
        (
            file_text(top="min_cases_reason = 3"),
            "'min_cases_reason' must be a non-empty string",
        ),
        (
            file_text(
                cases=[
                    GOOD_CASES[0].replace("expected = ", "colour = "),
                    *GOOD_CASES[1:],
                ]
            ),
            "needs 'expected' values",
        ),
    ],
    ids=[
        "top-level-key",
        "source-key",
        "case-key",
        "tolerance-key",
        "source-kind",
        "edge-type",
        "inputs-type",
        "reason-type",
        "no-expectation",
    ],
)
def test_the_loader_rejects_malformed_files(
    tmp_path: Path, text: str, needle: str
) -> None:
    assert_problem(problems_of(tmp_path, text), needle)


def test_the_loader_reports_every_fault_at_once(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text('model = "x"\nzzz = 1\naaa = 2\n', encoding="utf-8")
    with pytest.raises(GoldenError) as raised:
        load_golden(path)
    assert len(raised.value.problems) >= 4
    assert "unknown key 'aaa'" in str(raised.value)
    assert "missing key 'sources'" in str(raised.value)


def test_sources_and_cases_must_be_arrays_of_tables(tmp_path: Path) -> None:
    with pytest.raises(GoldenError, match="array of tables"):
        parse_golden({"model": "a.b", "sources": 3, "cases": []}, tmp_path / "x.toml")


def test_a_negative_tolerance_is_rejected(tmp_path: Path) -> None:
    extra = "tolerance = { price = { abs = -1.0 } }\n"
    text = file_text(cases=[GOOD_CASES[0] + extra, *GOOD_CASES[1:]])
    assert_problem(problems_of(tmp_path, text), "tolerance.price", "not negative")


def test_a_tolerance_needs_numbers(tmp_path: Path) -> None:
    extra = 'tolerance = { price = { abs = "wide" } }\n'
    text = file_text(cases=[GOOD_CASES[0] + extra, *GOOD_CASES[1:]])
    assert_problem(problems_of(tmp_path, text), "must be numbers")


# --- citations ----------------------------------------------------------------


def test_a_case_citing_an_undefined_source_fails(tmp_path: Path) -> None:
    cases = [case("ten_years", "nowhere", **at(0.05, 10)), *GOOD_CASES[1:]]
    assert_problem(
        problems_of(tmp_path, file_text(cases)), "undefined source 'nowhere'"
    )


def test_a_case_without_a_locator_fails_unless_its_source_is_an_identity(
    tmp_path: Path,
) -> None:
    cases = [case("ten_years", "paper", **at(0.05, 10), locator=None), *GOOD_CASES[1:]]
    assert_problem(problems_of(tmp_path, file_text(cases)), "no locator", "ten_years")
    # GOOD_CASES' second case is an identity without a locator, and passes.
    assert problems_of(tmp_path, file_text()) == []


def test_a_source_needs_a_link_unless_it_is_an_identity(tmp_path: Path) -> None:
    sources = PAPER.replace('doi = "10.1000/toy"\n', "") + IDENTITY
    assert_problem(
        problems_of(tmp_path, file_text(sources=sources)), "needs a url, doi or isbn"
    )


def test_a_duplicate_source_or_case_fails(tmp_path: Path) -> None:
    assert_problem(
        problems_of(tmp_path, file_text(sources=PAPER + PAPER + IDENTITY)),
        "source 'paper' is defined twice",
    )
    assert_problem(
        problems_of(tmp_path, file_text([*GOOD_CASES, GOOD_CASES[0]])),
        "case 'ten_years' is defined twice",
    )


def test_a_scaffold_placeholder_fails(tmp_path: Path) -> None:
    sources = (
        PAPER.replace(
            "Fisher, I. (1930). The Theory of Interest. Macmillan.", "TODO: cite it"
        )
        + IDENTITY
    )
    assert_problem(
        problems_of(tmp_path, file_text(sources=sources)), "still a placeholder"
    )


# --- how many cases, and an edge case -----------------------------------------


def test_fewer_than_three_cases_fail_without_a_reason(tmp_path: Path) -> None:
    text = file_text(GOOD_CASES[:2])
    assert_problem(problems_of(tmp_path, text), "2 case(s)", "min_cases_reason")


def test_a_recorded_reason_allows_fewer_cases(tmp_path: Path) -> None:
    text = file_text(
        GOOD_CASES[:2], top='min_cases_reason = "Only two published values exist."'
    )
    assert problems_of(tmp_path, text) == []


def test_no_edge_case_fails(tmp_path: Path) -> None:
    cases = [
        GOOD_CASES[0],
        case("five", "paper", **at(0.04, 5)),
        case("seven", "paper", **at(0.03, 7)),
    ]
    assert_problem(problems_of(tmp_path, file_text(cases)), "no case has edge = true")


def test_a_recorded_reason_stands_in_for_the_edge_case(tmp_path: Path) -> None:
    cases = [
        GOOD_CASES[0],
        case("five", "paper", **at(0.04, 5)),
        case("seven", "paper", **at(0.03, 7)),
    ]
    text = file_text(
        cases, top='min_cases_reason = "An identity has no degenerate input."'
    )
    assert problems_of(tmp_path, text) == []


# --- textbook values ----------------------------------------------------------


TEXTBOOK = """[[sources]]
key = "book"
kind = "textbook"
citation = "Bodie, Kane and Marcus (2014). Investments. McGraw-Hill."
isbn = "9780078034695"
"""


def textbook_file(sources: str, tolerance: str = "") -> str:
    book = case("book_case", "book", **at(0.05, 10), extra=tolerance)
    return file_text(
        [book, *GOOD_CASES[1:], GOOD_CASES[0]], sources=sources + PAPER + IDENTITY
    )


def test_a_textbook_source_needs_a_method_or_its_digits(tmp_path: Path) -> None:
    assert_problem(
        problems_of(tmp_path, textbook_file(TEXTBOOK)),
        "recomputed_with",
        "published_digits",
    )


def test_a_textbook_value_recomputed_independently_keeps_its_default_tolerance(
    tmp_path: Path,
) -> None:
    sources = TEXTBOOK + 'recomputed_with = "numpy_financial.pv"\n'
    assert problems_of(tmp_path, textbook_file(sources)) == []


def test_a_textbook_value_cannot_claim_more_than_it_published(tmp_path: Path) -> None:
    sources = TEXTBOOK + "published_digits = 2\n"
    assert_problem(
        problems_of(tmp_path, textbook_file(sources)),
        "book_case",
        "published to 2 decimal places",
        "at least 0.005",
    )


def test_a_textbook_value_may_loosen_its_tolerance_to_half_a_unit(
    tmp_path: Path,
) -> None:
    sources = TEXTBOOK + "published_digits = 2\n"
    tolerance = "tolerance = { price = { abs = 0.005 } }\n"
    assert problems_of(tmp_path, textbook_file(sources, tolerance)) == []


def test_a_textbook_tolerance_just_under_half_a_unit_fails(tmp_path: Path) -> None:
    sources = TEXTBOOK + "published_digits = 2\n"
    tolerance = "tolerance = { price = { abs = 0.004 } }\n"
    assert_problem(
        problems_of(tmp_path, textbook_file(sources, tolerance)), "book_case"
    )


def test_a_relative_tolerance_counts_at_the_value(tmp_path: Path) -> None:
    sources = TEXTBOOK + "published_digits = 2\n"
    loose = "tolerance = { price = { rel = 0.001 } }\n"  # 0.061 at 61.39
    assert problems_of(tmp_path, textbook_file(sources, loose)) == []
    tight = "tolerance = { price = { rel = 0.00001 } }\n"  # 0.0006
    assert_problem(problems_of(tmp_path, textbook_file(sources, tight)), "book_case")


# --- the expected fields ------------------------------------------------------


def test_an_expected_field_that_is_not_an_output_fails(tmp_path: Path) -> None:
    bad = case(
        "ten_years", "paper", inputs=at(0.05, 10)["inputs"], expected={"cost": 1.0}
    )
    assert_problem(
        problems_of(tmp_path, file_text([bad, *GOOD_CASES[1:]])),
        "cost is not an output of ZeroCouponOutputs",
        "outputs: price",
    )


def test_a_tolerance_for_a_field_that_is_not_an_output_fails(tmp_path: Path) -> None:
    extra = "tolerance = { cost = { abs = 1.0 } }\n"
    text = file_text([GOOD_CASES[0] + extra, *GOOD_CASES[1:]])
    assert_problem(problems_of(tmp_path, text), "cost is not an output")


def test_a_field_expected_and_expected_none_fails(tmp_path: Path) -> None:
    extra = 'expected_none = ["price"]\n'
    text = file_text([GOOD_CASES[0] + extra, *GOOD_CASES[1:]])
    assert_problem(problems_of(tmp_path, text), "both expected and expected_none")


def zero_case(tmp_path: Path, cases: Sequence[str]) -> Case:
    problems_of(tmp_path, file_text(cases))
    return load_golden(tmp_path / ZERO_PATH).cases[0]


def test_run_case_reports_a_field_that_is_not_an_output(tmp_path: Path) -> None:
    bad = case("c", "paper", inputs=at(0.05, 10)["inputs"], expected={"cost": 1.0})
    found = run_case(tm.zero_coupon, zero_case(tmp_path, [bad, *GOOD_CASES[1:]]))
    assert found == ["c: cost is not an output of ZeroCouponOutputs"]


# --- running a case -----------------------------------------------------------


def test_an_output_beyond_the_default_tolerance_fails(tmp_path: Path) -> None:
    wrong = case("c", "paper", inputs=at(0.05, 10)["inputs"], expected={"price": 61.4})
    found = run_case(tm.zero_coupon, zero_case(tmp_path, [wrong, *GOOD_CASES[1:]]))
    assert len(found) == 1
    assert "price expected 61.4" in found[0]
    assert "abs_tol 1e-09" in found[0]


def test_a_case_tolerance_replaces_the_default(tmp_path: Path) -> None:
    near = case(
        "c",
        "paper",
        inputs=at(0.05, 10)["inputs"],
        expected={"price": 61.4},
        extra="tolerance = { price = { abs = 0.01 } }\n",
    )
    assert run_case(tm.zero_coupon, zero_case(tmp_path, [near, *GOOD_CASES[1:]])) == []
    far = near.replace("abs = 0.01", "abs = 0.001")
    assert (
        len(run_case(tm.zero_coupon, zero_case(tmp_path, [far, *GOOD_CASES[1:]]))) == 1
    )


def test_a_missing_tolerance_component_is_zero(tmp_path: Path) -> None:
    almost = case(
        "c",
        "paper",
        inputs=at(0.05, 10)["inputs"],
        expected={"price": price(0.05, 10) + 1e-7},
        extra="tolerance = { price = { rel = 1e-12 } }\n",
    )
    assert (
        len(run_case(tm.zero_coupon, zero_case(tmp_path, [almost, *GOOD_CASES[1:]])))
        == 1
    )


def test_a_rejected_input_is_a_mismatch_not_a_crash(tmp_path: Path) -> None:
    bad = case(
        "c",
        "paper",
        inputs={"face_value": -1, "rate": 0.05, "years": 10},
        expected={"price": 1.0},
    )
    found = run_case(tm.zero_coupon, zero_case(tmp_path, [bad, *GOOD_CASES[1:]]))
    assert len(found) == 1
    assert found[0].startswith("c: the model rejected the inputs")


def test_the_runner_decides_how_the_model_runs(tmp_path: Path) -> None:
    calls: list[str] = []

    def runner(
        model: Model[Any, Any], inputs: Mapping[str, object]
    ) -> Result[Any, Any]:
        calls.append(model.id)
        return run_model(model, inputs)

    assert run_case(tm.zero_coupon, zero_case(tmp_path, GOOD_CASES), runner) == []
    assert calls == [ZERO]


# --- arrays, dates and undefined outputs --------------------------------------


def dated_file(expected: str, inputs: str, extra: str = "") -> str:
    one = f"""[[cases]]
id = "c"
source = "identity"
edge = true
inputs = {inputs}
{expected}
{extra}
"""
    return file_text(
        [one],
        sources=IDENTITY,
        model="foundations.toy_dated",
        top='min_cases_reason = "One case suffices for this toy."',
    )


def dated_problems(tmp_path: Path, text: str) -> tuple[list[str], Case]:
    problems = problems_of(tmp_path, text, rm.dated, "foundations/toy_dated.toml")
    return problems, load_golden(tmp_path / "foundations/toy_dated.toml").cases[0]


def test_dates_arrays_and_undefined_outputs_compare_exactly(tmp_path: Path) -> None:
    text = dated_file(
        "expected = { end = 2026-01-31, dates = [2026-01-31, 2026-01-31] }\n"
        'expected_none = ["per_day"]',
        "{ start = 2026-01-31, days = 0 }",
    )
    problems, golden_case = dated_problems(tmp_path, text)
    assert problems == []
    assert run_case(rm.dated, golden_case) == []


def test_a_wrong_date_a_wrong_array_and_a_defined_value_all_fail(
    tmp_path: Path,
) -> None:
    text = dated_file(
        "expected = { end = 2026-02-01, dates = [2026-01-31] }\n"
        'expected_none = ["per_day"]',
        "{ start = 2026-01-31, days = 30 }",
    )
    problems, golden_case = dated_problems(tmp_path, text)
    assert problems == []
    found = run_case(rm.dated, golden_case)
    assert [f.split(" expected")[0] for f in found] == [
        "c: end",
        "c: dates",
        "c: per_day",
    ]


def test_an_array_compares_item_by_item_within_tolerance(tmp_path: Path) -> None:
    balance = [100 * 1.05**t for t in range(4)]
    text = file_text(
        [
            f"""[[cases]]
id = "c"
source = "identity"
edge = true
inputs = {{ start = 100, rate = 0.05, periods = 3 }}
expected = {{ balance = {value(balance)}, final = {balance[-1]!r} }}
"""
        ],
        sources=IDENTITY,
        model="foundations.toy_growth",
        top='min_cases_reason = "One case suffices for this toy."',
    )
    path = "foundations/toy_growth.toml"
    assert problems_of(tmp_path, text, rm.growth, path) == []
    golden_case = load_golden(tmp_path / path).cases[0]
    assert run_case(rm.growth, golden_case) == []
    short = text.replace(value(balance), value(balance[:3]))
    problems_of(tmp_path, short, rm.growth, path)
    assert len(run_case(rm.growth, load_golden(tmp_path / path).cases[0])) == 1


# --- a family of calculations -------------------------------------------------


def time_value_file(calculation: str, extra: str = "") -> str:
    if calculation == "present_value":
        inputs = (
            '{ calculation = "present_value", future_value = 100, '
            "rate = 0.05, years = 10 }"
        )
        expected = f"{{ present_value = {price(0.05, 10)!r} }}"
    else:
        inputs = (
            '{ calculation = "future_value", present_value = 100, '
            "rate = 0.05, years = 10 }"
        )
        expected = f"{{ future_value = {100 * 1.05**10!r} }}"
    body = f"""[[cases]]
id = "c"
source = "identity"
edge = true
inputs = {inputs}
expected = {expected}
{extra}
"""
    return file_text(
        [body],
        sources=IDENTITY,
        model="foundations.toy_time_value",
        top='min_cases_reason = "One case per calculation."',
    )


@pytest.mark.parametrize("calculation", ["present_value", "future_value"])
def test_the_calculation_selects_the_outputs_a_case_may_name(
    tmp_path: Path, calculation: str
) -> None:
    path = "foundations/toy_time_value.toml"
    assert (
        problems_of(tmp_path, time_value_file(calculation), tm.time_value, path) == []
    )
    golden_case = load_golden(tmp_path / path).cases[0]
    assert run_case(tm.time_value, golden_case) == []


def test_an_output_of_another_calculation_fails(tmp_path: Path) -> None:
    text = time_value_file("present_value").replace(
        "expected = { present_value", "expected = { future_value"
    )
    found = problems_of(
        tmp_path, text, tm.time_value, "foundations/toy_time_value.toml"
    )
    assert_problem(found, "future_value is not an output of PresentValueOutputs")


def test_a_union_case_without_a_calculation_fails(tmp_path: Path) -> None:
    text = time_value_file("present_value").replace(
        'calculation = "present_value", ', ""
    )
    found = problems_of(
        tmp_path, text, tm.time_value, "foundations/toy_time_value.toml"
    )
    assert_problem(found, "need a 'calculation'", "future_value, present_value")


# --- the format document ---------------------------------------------------------


def test_the_readmes_example_follows_its_own_rules(tmp_path: Path) -> None:
    readme = (GOLDEN_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"```toml\n(.*?)```", readme, re.DOTALL)
    assert match is not None
    golden = parse_golden(tomllib.loads(match.group(1)), tmp_path / "example.toml")
    assert file_problems(golden, None) == []
    assert {s.kind for s in golden.sources} == {"official", "textbook", "identity"}
    assert any(case.edge for case in golden.cases)


# --- a nested output --------------------------------------------------------------


class Pair(ModelOutputs):
    low: Ratio = Field(ge=0, le=100, description="Low")
    high: Ratio = Field(ge=0, le=100, description="High")


class PairInputs(ModelInputs):
    x: Ratio = Field(ge=0, le=50, description="A number")


class NestedOutputs(ModelOutputs):
    pair: Pair = Field(description="A nested output")


def nested_compute(inputs: PairInputs) -> NestedOutputs:
    return NestedOutputs(pair=Pair(low=inputs.x, high=2 * inputs.x))


NESTED = Model(
    ModelSpec(
        id="foundations.nested",
        version=1,
        title="Nested",
        summary="A nested output.",
        inputs=PairInputs,
        outputs=NestedOutputs,
    ),
    nested_compute,
)


def nested_case(tmp_path: Path, expected: str) -> Case:
    body = f"""[[cases]]
id = "c"
source = "identity"
edge = true
inputs = {{ x = 10 }}
expected = {{ pair = {expected} }}
"""
    text = file_text(
        [body],
        sources=IDENTITY,
        model="foundations.nested",
        top='min_cases_reason = "One case suffices for this toy."',
    )
    path = "foundations/nested.toml"
    assert problems_of(tmp_path, text, NESTED, path) == []
    return load_golden(tmp_path / path).cases[0]


def test_a_nested_output_compares_field_by_field(tmp_path: Path) -> None:
    assert run_case(NESTED, nested_case(tmp_path, "{ low = 10.0, high = 20.0 }")) == []
    wrong = nested_case(tmp_path, "{ low = 10.0, high = 21.0 }")
    assert len(run_case(NESTED, wrong)) == 1
    missing = nested_case(tmp_path, "{ low = 10.0 }")
    assert len(run_case(NESTED, missing)) == 1
