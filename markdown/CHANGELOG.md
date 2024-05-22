# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
