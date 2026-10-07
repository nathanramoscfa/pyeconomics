# tests/unit/test_version.py
"""``pyeconomics.__version__`` comes from the installed distribution."""

from importlib.metadata import version

import pyeconomics


def test_version_equals_distribution_metadata() -> None:
    assert pyeconomics.__version__ == version("pyeconomics")


def test_version_is_a_1_0_0_release() -> None:
    assert pyeconomics.__version__.startswith("1.0.0")
