# docs/conftest.py
# Copyright 2026 Nathan Ramos, CFA
# SPDX-License-Identifier: Apache-2.0
"""Run only authored site examples, with pytest's socket isolation."""

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser

collect_ignore = ["conf.py", "_ext"]
# MyST-NB cells execute in Sphinx; generated model pages contain JSON examples.
pytest_collect_file = Sybil(
    parsers=[PythonCodeBlockParser()],
    filenames=[
        "index.md",
        "installation.md",
        "quickstart.md",
        "conventions.md",
        "results.md",
        "errata.md",
        "notices.md",
        "changelog.md",
    ],
    excludes=["roadmap/*", "adr/*", "releases/*", "reference/*", "_build/*"],
).pytest()
