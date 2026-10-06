# ADR-0010: Python support policy

- Status: Accepted
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6 and 1.2; §2 gap 13

## Context and problem

The published 0.2.x package declares `Requires-Python >=3.11, <3.13`. That
excludes Python 3.13 and 3.14. Meanwhile its CI still tests 3.10, which
reached end of life on 2026-10-01 [S1] (ROADMAP §2, gap 13).

The 1.0 package needs a floor, a ceiling policy and a CI matrix that will
not rot the same way. The floor is set mostly by the scientific stack the
models need:

| Package | Latest release | `requires_python` |
|---------|----------------|-------------------|
| NumPy | 2.5.3 (2026-09-06) | `>=3.12` [S3] |
| SciPy | 1.18.1 (2026-08-21) | `>=3.12` [S4] |
| pandas | 3.0.6 (2026-09-17) | `>=3.11` [S5] |

The state of CPython itself, from the devguide [S1]:

| Version | Status | End of life |
|---------|--------|-------------|
| 3.10 | End of life | 2026-10-01 |
| 3.11 | Security fixes only | 2027-10 |
| 3.12 | Security fixes only | 2028-10 |
| 3.13 | Security fixes only | 2029-10 |
| 3.14 | Bugfix | 2030-10 |
| 3.15 | Pre-release | 2031-10 |

Python 3.15.0 final is expected on 2026-10-09 [S2]. The latest release at
the access date is 3.15.0rc3, from 2026-10-02 [S2].

SPEC 0, the Scientific Python ecosystem's support schedule, drops a Python
version three years after its first release and a core package two years
after its release [S6]. Its table drops Python 3.12 in 2026 Q4, so from now
it lists 3.13 and newer [S6]. NumPy and SciPy have not yet raised their
floors to 3.13 [S3][S4].

## Decision drivers

- Install on every Python the scientific stack supports, and on no Python
  it does not.
- No upper cap: a `<3.N` cap makes a package uninstallable on the next
  Python for no reason, as 0.2.x showed.
- The core runs in Pyodide and xlwings Lite (ADR-0002). Pyodide 314.0.7
  ships Python 3.14.2 [S7].
- One rule the maintainer can apply mechanically, without reopening this
  ADR at every Python release.

## Considered options

1. **`requires-python >=3.12` now, raised as NumPy and SciPy raise theirs,
   under SPEC 0.** Matches the floors the stack forces today.
2. **`>=3.13` now, following SPEC 0's calendar to the letter.** SPEC 0
   drops 3.12 this quarter [S6]. But NumPy 2.5 and SciPy 1.18 still
   support 3.12, so this would turn away 3.12 users the stack still
   serves, with nothing gained.
3. **`>=3.11`, matching pandas.** NumPy 2.5 and SciPy 1.18 need 3.12, so a
   3.11 user could install pyeconomics only with older NumPy and SciPy.
   That splits the tested matrix for one release line.

## Decision outcome

Chosen option: **1**, because it follows the stack the models depend on.
The stack follows SPEC 0, so pyeconomics inherits SPEC 0's schedule
without running ahead of NumPy and SciPy.

**Floor.**

- `requires-python = ">=3.12"`, with no upper bound.
- The floor is the higher of the floors of the newest NumPy and SciPy
  releases pyeconomics supports.
- When either raises its floor, pyeconomics raises its own in its next
  minor release (a minor release, per ADR-0003), with a changelog entry.
- SPEC 0 already lists 3.12 as dropped, so the move to `>=3.13` is
  expected within the 1.0 pre-release series. The date is TBD, set by the
  first NumPy or SciPy release that requires 3.13.

**CI matrix.**

- Python 3.12, 3.13 and 3.14 on Ubuntu, Windows and macOS.
- 3.15 is added when it is final (expected 2026-10-09 [S2]), together with
  its trove classifier.
- A new Python version joins the matrix at its final release.
- A dropped one leaves the matrix in the same change that raises the
  floor.

**Classifiers.** One `Programming Language :: Python :: 3.N` classifier
for each version in the CI matrix, and no others.

### Consequences

Good:

- pyeconomics installs wherever NumPy and SciPy do, and nowhere they do
  not.
- No cap means a new Python works on release day if the stack does.
- The rule is mechanical: watch two packages' `requires_python`.

Bad:

- 3.11 users, still in security support until 2027-10 [S1], cannot
  install 1.0. 0.2.x stays available for them until its end of life
  (ADR-0003).
- Raising the floor in a minor release can surprise a user on an old
  Python. pip's `Requires-Python` check keeps them on the last compatible
  release rather than breaking them.
- CI time grows with each Python version in the matrix.

### Confirmation

| Check | Built in |
|-------|----------|
| `requires-python = ">=3.12"`, no upper bound, in `pyproject.toml` | Phase 1 Step 7 |
| CI test matrix: 3.12, 3.13 and 3.14 on Ubuntu, Windows and macOS, with 3.15 once final (or an open issue to add it at its release) | Phase 1 Step 10 |
| Classifiers equal the matrix: `verify-phase01.sh` static check 35 compares them | Phase 1 Step 12 (added to its task by this step) |
| Release checklist: each phase's release step re-checks NumPy's and SciPy's `requires_python` and raises the floor if either moved | Phases 2–5 release steps |

## More information

- Related: ADR-0002 (pure-Python core for Pyodide and xlwings Lite),
  ADR-0003 (floor changes ship in minor releases).
- Sources:
  - [S1] Python devguide, "Status of Python versions",
    https://devguide.python.org/versions/, accessed 2026-10-05.
  - [S2] PEP 790, Python 3.15 Release Schedule (3.15.0 final expected
    2026-10-09), https://peps.python.org/pep-0790/; python.org release
    list (3.15.0rc3, 2026-10-02),
    https://www.python.org/api/v2/downloads/release/, both accessed
    2026-10-05.
  - [S3] PyPI, `numpy` 2.5.3, `requires_python >=3.12`,
    https://pypi.org/pypi/numpy/json, accessed 2026-10-05.
  - [S4] PyPI, `scipy` 1.18.1, `requires_python >=3.12`,
    https://pypi.org/pypi/scipy/json, accessed 2026-10-05.
  - [S5] PyPI, `pandas` 3.0.6, `requires_python >=3.11`,
    https://pypi.org/pypi/pandas/json, accessed 2026-10-05.
  - [S6] SPEC 0, Minimum Supported Dependencies,
    https://scientific-python.org/specs/spec-0000/, accessed 2026-10-05.
  - [S7] Pyodide 314.0.7 (2026-09-14), Python 3.14.2,
    https://pyodide.org/en/stable/project/changelog.html, accessed
    2026-10-05.
