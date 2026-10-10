# tests/golden/test_sources.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The citation guard: no source may be the CFA Program curriculum.

ROADMAP section 5 "Legal & brand guardrails" bars the curriculum's readings,
learning outcome statements, practice problems, mock exams and worked examples as
a source. The Financial Analysts Journal is peer-reviewed and stays allowed.
These tests scan every golden source and every model reference, and hold the guard
itself to both answers: it must reject the curriculum and accept the journal.
"""

from __future__ import annotations

import pytest
from _citations import curriculum_problem
from _loader import audit

from pyeconomics.core.registry import installed

REGISTRY = installed()

ALLOWED = [
    (
        "Black, F. and Litterman, R. (1992). Global Portfolio Optimization. "
        "Financial Analysts Journal, 48(5), 28-43."
    ),
    "Financial Analysts Journal, Vol. 48 No. 5, Table 2",
    "https://www.cfainstitute.org/research/financial-analysts-journal/1992/x",
    "https://rpc.cfainstitute.org/research/financial-analysts-journal/2014/y",
    "Hull, J. (2022). Options, Futures, and Other Derivatives. Pearson.",
    "https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/",
    "CFA Institute Research Foundation monograph on tail risk",
    "https://doi.org/10.2469/faj.v48.n5.28",
    (
        "Macaulay, F. (1938). Some Theoretical Problems Suggested by the Movements "
        "of Interest Rates. NBER."
    ),
    "Loss given default is 45%",
    "The LOSS function is convex",
]

REJECTED = [
    "CFA Program Curriculum, Level II, Reading 23",
    "CFA® Program curriculum",
    "CFA Institute (2024). Level III Fixed Income, Reading 12",
    "Learning outcome statement 4.b of the reading",
    "the LOS in the reading",
    "Practice problems at the end of the reading",
    "End-of-reading questions, Q7",
    "A CFA mock exam, morning session",
    "Schweser Notes, Book 4",
    "Kaplan Qbank item 12",
    "https://www.cfainstitute.org/programs/cfa/curriculum",
    "https://www.cfainstitute.org/-/media/documents/book/rf-lit-review/x.pdf",
    "https://cfainstitute.org/en/membership",
    "https://rpc.cfainstitute.org/policy-and-research/x",
    "See www.cfainstitute.org/en/research/foundation for the table",
    "Level II, Reading 23: Yield-Based Bond Duration Measures",
    "Reading 23, Level II",
    "CFA Institute\nLevel II Reading 23",
    "Level 3 Reading 7",
    "CFAI Level II Reading 23",
    "Study Session 7, Example 4",
    "https://cfainstitute.org./programs/cfa",
]


@pytest.mark.parametrize("text", ALLOWED)
def test_the_guard_allows_the_journal_and_independent_sources(text: str) -> None:
    assert curriculum_problem([text]) is None


@pytest.mark.parametrize("text", REJECTED)
def test_the_guard_rejects_the_curriculum(text: str) -> None:
    assert curriculum_problem([text]) is not None


def test_the_guard_reads_every_field_and_skips_missing_ones() -> None:
    assert curriculum_problem([None, "fine", None]) is None
    assert curriculum_problem(["fine", None, "CFA Program Curriculum"]) is not None


def test_a_journal_link_on_cfainstitute_org_is_allowed_a_curriculum_link_is_not() -> (
    None
):
    journal = "https://www.cfainstitute.org/research/financial-analysts-journal/1992/x"
    assert curriculum_problem([journal]) is None
    other = "https://www.cfainstitute.org/research/foundation/2020/x"
    problem = curriculum_problem([other])
    assert problem is not None
    assert "Financial Analysts Journal" in problem


def test_no_golden_source_or_locator_cites_the_curriculum() -> None:
    found = []
    for golden in audit(REGISTRY).files:
        name = golden.path.name
        for source in golden.sources:
            fields = [
                source.citation,
                source.url,
                source.doi,
                source.isbn,
                source.recomputed_with,
            ]
            if (problem := curriculum_problem(fields)) is not None:
                found.append(f"{name}: source {source.key!r} {problem}")
        found += [
            f"{name}: case {case.id!r} locator {problem}"
            for case in golden.cases
            if (problem := curriculum_problem([case.locator, case.note])) is not None
        ]
    assert not found, "\n".join(found)


def test_no_model_reference_cites_the_curriculum() -> None:
    found = []
    for model in REGISTRY.models():
        for reference in model.spec.references:
            fields = [
                reference.citation,
                reference.url,
                reference.doi,
                reference.isbn,
                reference.locator,
            ]
            if (problem := curriculum_problem(fields)) is not None:
                found.append(f"{model.id}: reference {reference.key!r} {problem}")
    assert not found, "\n".join(found)
