# tests/golden/_citations.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""The citation guard: no source may be the CFA Program curriculum.

ROADMAP section 5 "Legal & brand guardrails" bars the CFA Program's readings,
learning outcome statements, practice problems, mock exams and worked examples
as a source of any value or formula. The Financial Analysts Journal, which CFA
Institute publishes, is peer-reviewed and stays allowed, so a link into
``cfainstitute.org`` passes only when its path is the journal's.

:func:`curriculum_problem` reads the text fields of one source or reference. It
is a guard against a slip, not a proof of provenance: a reviewer still reads
every new source listed in the pull request body.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = ["curriculum_problem"]

#: The host whose links are held to the journal's path.
_CFA_HOST: Final = "cfainstitute.org"

#: The path segment that marks the Financial Analysts Journal on that host.
_JOURNAL_PATH: Final = "financial-analysts-journal"

_LINK: Final = re.compile(
    r"(?:https?://)?(?:[\w-]+\.)*cfainstitute\.org[^\s\"'<>)]*", re.IGNORECASE
)

#: Phrases that name the curriculum or its derivatives, with what to call them.
#: ``(?-i:...)`` keeps an acronym case-sensitive inside a case-insensitive pattern.
_PATTERNS: Final = (
    (re.compile(r"\bcurricul", re.IGNORECASE), "the curriculum"),
    (re.compile(r"\bCFA\s*(?:®)?\s+Program", re.IGNORECASE), "the CFA Program"),
    (
        re.compile(r"\blearning\s+outcome", re.IGNORECASE),
        "a learning outcome statement",
    ),
    (re.compile(r"(?-i:\bLOS\b)"), "a learning outcome statement"),
    (
        re.compile(r"\bpractice\s+(?:problem|question|exam)", re.IGNORECASE),
        "practice problems",
    ),
    (re.compile(r"\bmock\s+exam", re.IGNORECASE), "a mock exam"),
    (
        re.compile(r"\bend[- ]of[- ]reading\b", re.IGNORECASE),
        "end-of-reading questions",
    ),
    (re.compile(r"\bq-?bank\b", re.IGNORECASE), "a question bank"),
    (re.compile(r"\bSchweser\b", re.IGNORECASE), "curriculum-derived study notes"),
    (re.compile(r"(?-i:\bCFAI\b)"), "a CFAI curriculum reference"),
    (re.compile(r"\bstudy\s+session\b", re.IGNORECASE), "a study session"),
    (
        re.compile(
            r"(?=.*\bLevel\s+(?:I{1,3}|[123])\b)(?=.*\bReading\s+\d+)",
            re.IGNORECASE | re.DOTALL,
        ),
        "a curriculum level and reading",
    ),
)


def _link_problem(link: str) -> str | None:
    """Reject a link into cfainstitute.org that is not the journal's."""
    parts = urlsplit(link if "://" in link else f"https://{link}")
    host = (parts.hostname or "").lower().rstrip(".")
    if (host == _CFA_HOST or host.endswith(f".{_CFA_HOST}")) and (
        _JOURNAL_PATH not in parts.path.lower()
    ):
        return (
            f"links to {link!r} on cfainstitute.org, which is allowed only for the "
            "Financial Analysts Journal"
        )
    return None


def curriculum_problem(fields: Iterable[str | None]) -> str | None:
    """Return why a source cites the CFA Program curriculum, or ``None`` if it does not.

    Parameters
    ----------
    fields
        The text of the source: its citation, locator, url, doi, isbn and the
        like. ``None`` entries are skipped.

    Examples
    --------
    >>> curriculum_problem(["Black and Litterman (1992). Financial Analysts Journal."])
    >>> curriculum_problem(["CFA Program Curriculum, Level II, Reading 23"])
    'cites the curriculum'
    """
    text = " ".join(field for field in fields if field)
    for link in _LINK.findall(text):
        if (problem := _link_problem(link)) is not None:
            return problem
    for pattern, name in _PATTERNS:
        if pattern.search(text):
            return f"cites {name}"
    return None
