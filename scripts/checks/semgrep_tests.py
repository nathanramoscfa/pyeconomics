# scripts/checks/semgrep_tests.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Run the project semgrep rules' tests, and fail if any rule goes untested.

`semgrep --test` pairs a rule file with the test file of the same stem. With
the rules in .semgrep/rules/ and their tests in .semgrep/tests/, the bare
`semgrep --test .semgrep/` pairs nothing: it prints "No unit tests found" and
exits 0, and a renamed rule would pass the same way. This wrapper fails unless
every rule file has a test file, every rule id has at least one `ruleid:` and
one `ok:` case, and every case passes.

It runs `semgrep --test --config <rule> <test>` once per pair, one after
another. A single `semgrep --test` over the whole directory starts one worker
per rule file, and on Windows those workers race to rewrite
~/.semgrep/settings.yml and fail at random.

Usage, from the repository root (the `semgrep-test` prek hook runs it in an
environment with semgrep installed):

    python scripts/checks/semgrep_tests.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess  # nosec B404 # runs the semgrep CLI with a fixed argument list
import sys
from pathlib import Path

RULES = Path(".semgrep/rules")
TESTS = Path(".semgrep/tests")
RULE_ID = re.compile(r"^\s*-\s*id:\s*([\w.-]+)\s*$", re.MULTILINE)

Pair = tuple[Path, Path, list[str]]  # rule file, test file, rule ids


def annotated(text: str, kind: str, rule_id: str) -> bool:
    """Return whether a test file carries a `# <kind>: ...<rule_id>...` comment."""
    pattern = rf"#\s*{kind}:\s*(?:[\w.-]+\s*,\s*)*{re.escape(rule_id)}\b"
    return re.search(pattern, text) is not None


def pair_rules_with_tests() -> tuple[list[Pair], list[str]]:
    """Pair each rule file with its test files, checking the annotations."""
    rule_files = sorted([*RULES.glob("*.yaml"), *RULES.glob("*.yml")])
    if not rule_files:
        return [], [f"{RULES.as_posix()}: no rule files"]
    pairs: list[Pair] = []
    problems = []
    for rule_file in rule_files:
        ids = RULE_ID.findall(rule_file.read_text(encoding="utf-8"))
        if not ids:
            problems.append(f"{rule_file.as_posix()}: no rule id")
        tests = sorted(
            t for t in TESTS.glob(f"{rule_file.stem}.*") if t.suffix != rule_file.suffix
        )
        if not tests:
            problems.append(
                f"{rule_file.as_posix()}: no test file named {rule_file.stem}.*"
            )
        text = "\n".join(t.read_text(encoding="utf-8") for t in tests)
        problems.extend(
            f"{rule_file.as_posix()}: no `# {kind}: {rule_id}` case"
            for rule_id in ids
            for kind in ("ruleid", "ok")
            if tests and not annotated(text, kind, rule_id)
        )
        pairs += [(rule_file, test, ids) for test in tests]
    return pairs, problems


def run_pair(
    semgrep: str, rule_file: Path, test: Path, rule_ids: list[str]
) -> list[str]:
    """Run `semgrep --test` on one rule file and one test file."""
    command = [
        semgrep,
        "--test",
        "--json",
        "--metrics=off",
        "--disable-version-check",
        "--config",
        rule_file.as_posix(),
        test.as_posix(),
    ]
    # bandit B603 / ruff S603: the arguments are fixed, semgrep is resolved by
    # shutil.which, and no shell is involved.
    result = subprocess.run(  # nosec B603  # noqa: S603
        command, capture_output=True, text=True, check=False
    )
    label = f"{rule_file.name} on {test.name}"
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        stderr = result.stderr.strip()[-2000:]
        return [f"{label}: semgrep exited {result.returncode}: {stderr}"]

    problems = [
        f"{label}: {key.replace('_', ' ')}: {report[key]}"
        for key in ("config_missing_tests", "config_with_errors")
        if report.get(key)
    ]
    checks = {
        rule_id: check
        for outcome in report.get("results", {}).values()
        for rule_id, check in outcome.get("checks", {}).items()
    }
    for rule_id in rule_ids:
        check = checks.get(rule_id)
        if check is None:
            problems.append(f"{label}: semgrep ran no test for {rule_id}")
        elif not check.get("passed"):
            for lines in check.get("matches", {}).values():
                expected, reported = (
                    lines.get("expected_lines"),
                    lines.get("reported_lines"),
                )
                problems.append(
                    f"{label}: {rule_id} expected lines {expected}, got {reported}"
                )
            problems += [
                f"{label}: {rule_id}: {error}" for error in check.get("errors", [])
            ]
            if not check.get("matches") and not check.get("errors"):
                problems.append(f"{label}: {rule_id} failed")
        elif not any(
            m.get("expected_lines") for m in check.get("matches", {}).values()
        ):
            problems.append(f"{label}: no `ruleid:` case for {rule_id} was exercised")
    if result.returncode != 0 and not problems:
        problems.append(f"{label}: semgrep exited {result.returncode}")
    return problems


def main() -> int:
    """Run every rule's tests; return the process exit status."""
    pairs, problems = pair_rules_with_tests()
    semgrep = shutil.which("semgrep")
    if semgrep is None:
        problems.append("semgrep is not installed in this environment")
    if not problems and semgrep is not None:
        for rule_file, test, rule_ids in pairs:
            problems += run_pair(semgrep, rule_file, test, rule_ids)
    if problems:
        print("Semgrep rule tests failed:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    rules = {rule_id for _, _, rule_ids in pairs for rule_id in rule_ids}
    print(f"semgrep-test: {len(rules)} rules; every ruleid and ok case passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
