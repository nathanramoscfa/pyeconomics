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

- Governance and community files: README with status banner and notices,
  CONTRIBUTING, Contributor Covenant 3.0 Code of Conduct, SECURITY policy,
  CITATION.cff, CODEOWNERS, issue forms, defect-class labels, `AGENTS.md` and
  `CLAUDE.md` for coding agents, and funding hooks (`.github/FUNDING.yml`,
  `funding.json`).

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
