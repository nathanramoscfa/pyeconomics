# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6] - 2026-10-05
### Security
- The FRED API key is no longer written to the log. Versions 0.2.0 to
  0.2.5 logged the key at DEBUG level whenever `FredClient` was created,
  including the client created when `pyeconomics` is imported, whether the
  key came from the `api_key` argument, the `FRED_API_KEY` environment
  variable or the system keyring. If you ran pyeconomics with DEBUG logging
  enabled and those logs were stored or shared, rotate your FRED API key at
  https://fredaccount.stlouisfed.org/apikeys. Advisory:
  https://github.com/nathanramoscfa/pyeconomics/security/advisories/GHSA-j6rp-vwwv-jrr8.
- A regression test now fails if the key reaches any log record.
- Releases are published from GitHub Actions through PyPI Trusted Publishing,
  with attestations; no long-lived PyPI token exists.

### Deprecated
- 0.2.x receives security fixes only and reaches end-of-life when
  pyeconomics 1.0.0 is released.

### Removed
- `pyeconomics/__version__.py`, written at build time by the old release
  workflow, is no longer shipped; use
  `importlib.metadata.version("pyeconomics")`.

### Known issues
- The pinned runtime requirements carry published advisories that 0.2.6
  does not change: jupyterlab 4.1.x (14 advisories in the JupyterLab server
  and front end), pytest 8.2.x (one local denial of service while pytest
  runs) and setuptools 68.2.x (three, in `package_index` downloads and sdist
  builds). pyeconomics does not import or run any of them.
- Installing pyeconomics downgrades an environment's setuptools to 68.2.x.
- If you run JupyterLab or build packages in the same environment, install
  pyeconomics in its own virtual environment.

## [0.2.5] - 2024-05-30
### Added
- Establishment of the first stable and tested version of PyEconomics.

## [0.2.0] - 2024-05-21
### Added
- Implementation of well-known monetary policy rules:
  - Taylor Rule
  - Balanced Approach Rule
  - First Difference Rule
- Cache management for API calls.
- Basic project structure and organization:
  - `pyeconomics` package with submodules for `api`, `models`, and `utils`.
  - `tests` directory with unit tests for the implemented models and utilities.
  - `examples` directory with Jupyter Notebooks demonstrating usage of the monetary policy rules.
  - `docs` directory with initial Sphinx documentation setup.
- Detailed `README.md` with project overview, features, installation instructions, usage examples, and roadmap.
- Configuration files for development and build tools:
  - `.gitignore` for ignoring unnecessary files in Git.
  - `.dockerignore` for optimizing Docker build context.
  - `.coveragerc` for configuring test coverage reporting.
  - `.readthedocs.yml` for configuring Read the Docs documentation builds.
  - GitHub Actions workflows for continuous integration:
    - `docs.yml` for building documentation.
    - `release.yml` for building and releasing the package.
    - `tests.yml` for running tests and reporting coverage.

## [0.1.0] - 2024-05-05
### Added
- Initial commit of the PyEconomics project to secure the project name.
