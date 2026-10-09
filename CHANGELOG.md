# Changelog

All notable changes to pyeconomics 1.0 and later are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and versions follow [PEP 440](https://peps.python.org/pep-0440/) with
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) meaning (ADR-0003).
Pre-releases of 1.0.0 carry no stability promise. Deprecations are listed under
"Deprecated" at least one minor release before their removal.

The 0.2.x history (0.1.0 to 0.2.6) is in the
[0.2.x changelog on `legacy/0.2.x`](https://github.com/pyeconomics-dev/pyeconomics/blob/legacy/0.2.x/markdown/CHANGELOG.md).

## [Unreleased]

### Added

- Date arithmetic with end-of-month rules, six day-count conventions including
  irregular ICMA coupon periods, backward coupon schedules with short or long
  front stubs, and five holiday calendars with business-day adjustments.
- `holidays>=0.106` as an audited runtime dependency; QuantLib as a test-only
  oracle for day counts, schedules and calendars. The installed-wheel and
  Pyodide smoke checks exercise the date layer.
- Governance and community files: README with status banner and notices,
  CONTRIBUTING, Contributor Covenant 3.0 Code of Conduct, SECURITY policy,
  CITATION.cff, CODEOWNERS, issue forms, defect-class labels, `AGENTS.md` and
  `CLAUDE.md` for coding agents, and funding hooks (`.github/FUNDING.yml`,
  `funding.json`).
- ADR-0008, numerical conventions: decimal rates, the unit vocabulary and
  default bounds, compounding, day counts and calendars, tolerances, seeded
  randomness, arrays and tabular data, pandas 3 semantics, non-finite and
  undefined results, root finding, canonical JSON numbers, the error and
  warning taxonomy, and the runtime floors.
- `pyeconomics.core`, the date-free conventions: unit kinds with `Annotated`
  markers (`Rate`, `Money`, `Years` and the rest) that export `x-unit` and
  reject NaN and infinity; percent and basis-point converters and
  formatting; `Frequency`, `Compounding` and rate and discount-factor
  conversions; `Tolerance`; seeded `PCG64` generators; a bracketed Brent
  root finder; and the exceptions (`PyeconomicsError` and its subclasses)
  and warnings (`ModelWarning`, `PyeconomicsDeprecationWarning`, a
  `FutureWarning`).
- Runtime dependencies: pydantic 2.12, NumPy 2.4, SciPy 1.18 and pandas 3.0
  or later (floors Pyodide 314.0.7 can satisfy), with reviewed licence
  exceptions for numpy, scipy, pandas and python-dateutil.
- `scripts/smoke.py` and a `pyodide` CI job that installs the wheel in
  Pyodide 314.0.7 and runs it, beside the clean-venv run in the package job.

### Changed

- The version on `main` is `1.0.0a1.dev1`, the milestone it builds towards
  (Phase 2's version rule); `CITATION.cff` names the same version.

## [1.0.0.dev1] - 2026-10-07

The 1.0 skeleton and its publishing pipeline, released to TestPyPI only.

### Added

- `src/pyeconomics/` package skeleton with a typed marker, version
  `1.0.0.dev1` read through `importlib.metadata`, and the ADR-0002 extras as
  empty placeholders.
- A PEP 621 `pyproject.toml` on the `uv_build` backend, requiring Python 3.12
  or later, with `uv.lock` and an exported `pylock.toml`.
- Architecture decision records ADR-0001 to ADR-0007, ADR-0009 and ADR-0010.
- Per-step security gate run by prek: gitleaks, bandit, semgrep with project
  rules, `pip-audit` and a runtime licence allowlist, mirrored in CI with
  trufflehog, CodeQL, zizmor, dependency review and OpenSSF Scorecard.
- Quality toolchain: ruff with every rule family, mypy strict, pytest with
  hypothesis, syrupy, pytest-benchmark, branch coverage, pytest-socket and
  doctests.
- CI on Ubuntu, Windows and macOS for Python 3.12 to 3.14, with package,
  lockfile, pull-request-title and DCO checks.
- Release workflow publishing through PyPI Trusted Publishing with
  attestations, and a post-publish install smoke test.

### Changed

- Licence: Apache-2.0 from 1.0. Releases up to and including 0.2.x remain MIT.
- The repository moved to `pyeconomics-dev/pyeconomics`.

### Removed

- The 0.2.x code from `main`; it continues on `legacy/0.2.x`.

[Unreleased]: https://github.com/pyeconomics-dev/pyeconomics/compare/v1.0.0.dev1...HEAD
[1.0.0.dev1]: https://github.com/pyeconomics-dev/pyeconomics/tree/v1.0.0.dev1
