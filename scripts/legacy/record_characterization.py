# scripts/legacy/record_characterization.py
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#     # The published 0.2.x release under characterization. Its wheel pulls
#     # in its whole requirements.txt (jupyterlab, openai, sphinx, ...); no
#     # extra pin is needed for it to import and run on CPython 3.12.
#     "pyeconomics==0.2.6",
# ]
#
# [tool.uv]
# # Freezes the resolution so every run installs the same distributions
# # (0.2.6 reached PyPI at 2026-10-06T00:17Z; nothing later is admitted).
# exclude-newer = "2026-10-07T00:00:00Z"
# ///
"""Record characterization fixtures for the published pyeconomics 0.2.6.

Runs the four 0.2.x monetary-policy rules over a deterministic grid of
explicit inputs, the combined estimates table over a subset of it, and each
historical_* function over one synthetic monthly panel, with every network
path blocked. Writes tests/fixtures/legacy/: one JSON file per rule, per
historical variant and for the combined table, plus manifest.json and
README.md.

Usage (from the repository root):

    uv run --no-config --script scripts/legacy/record_characterization.py
    uv run --no-config --script scripts/legacy/record_characterization.py --check

`--no-config` keeps a user-level uv configuration (for example a package
firewall index) out of the resolution. `--check` re-records into a temporary
directory and fails on any byte difference from the committed fixtures.
"""

# Network block: installed before anything else is imported so that neither
# 0.2.6 nor its dependencies can open a connection while recording.
import socket


class _BlockedSocket(socket.socket):
    """socket.socket replacement that refuses to be created.

    A subclass, not a plain function: the standard library subclasses
    socket.socket at import time (ssl.SSLSocket), which a function breaks.
    """

    def __init__(self, *args, **kwargs):
        raise OSError("network access is blocked while recording fixtures")


def _blocked(*args, **kwargs):
    raise OSError("network access is blocked while recording fixtures")


socket.socket = _BlockedSocket
socket.create_connection = _blocked
socket.getaddrinfo = _blocked

import os  # noqa: E402

# 0.2.6 builds a FRED client at import and needs some key; this one is
# deliberately not shaped like a real one (32 lowercase hex characters).
os.environ["FRED_API_KEY"] = "fixture-recorder-no-network"
os.environ["MPLBACKEND"] = "Agg"

import argparse  # noqa: E402
import filecmp  # noqa: E402
import hashlib  # noqa: E402
import importlib.metadata  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import pandas as pd  # noqa: E402

import pyeconomics  # noqa: E402
from pyeconomics import (  # noqa: E402
    BalancedApproachRuleParameters,
    EconomicIndicators,
    FirstDifferenceRuleParameters,
    TaylorRuleParameters,
    balanced_approach_rule,
    calculate_historical_policy_rates,
    calculate_policy_rule_estimates,
    first_difference_rule,
    fred_client,
    historical_balanced_approach_rule,
    historical_first_difference_rule,
    historical_taylor_rule,
    taylor_rule,
)

PYECONOMICS_VERSION = "0.2.6"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "legacy"

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

GRID = {
    "inflation": [-1.0, 0.0, 2.0, 3.5, 9.0],
    "unemployment": [3.5, 4.2, 6.0, 10.0],
    "natural_rate": [4.2],
    "long_run_real_rate": [0.5, 2.0],
    "current_fed_rate": [0.125, 2.5, 5.375],
    "lagged_unemployment_and_natural_rate": [[4.0, 4.2], [6.5, 4.2]],
    "rho": [0.0, 0.7, 0.85],
    "apply_elb": [False, True],
}

# One non-default value per parameter, run over CORNER_GRID.
CORNERS = {
    "alpha": 1.0,
    "beta": 1.0,
    "okun_factor": 1.5,
    "inflation_target": 2.5,
}

CORNER_GRID = {
    "inflation": GRID["inflation"],
    "unemployment": GRID["unemployment"],
    "natural_rate": [4.2],
    "long_run_real_rate": [2.0],
    "current_fed_rate": [2.5],
    "lagged_unemployment_and_natural_rate": (
        GRID["lagged_unemployment_and_natural_rate"]),
    "rho": [0.0, 0.7],
    "apply_elb": [False, True],
}

COMBINED_GRID = {
    "inflation": [-1.0, 2.0, 9.0],
    "unemployment": [3.5, 10.0],
    "natural_rate": [4.2],
    "long_run_real_rate": [2.0],
    "current_fed_rate": [0.125, 5.375],
    "lagged_unemployment_and_natural_rate": [[4.0, 4.2]],
    "rho": [0.0, 0.85],
    "apply_elb": [False, True],
}

# Historical runs: each historical_* function once per configuration.
HISTORICAL_CONFIGS = [
    {"rho": 0.0, "apply_elb": False},
    {"rho": 0.7, "apply_elb": True},
]

RULES = {
    "taylor_rule": {
        "function": taylor_rule,
        "params": TaylorRuleParameters,
        "extra": {},
        "uses_real_rate": True,
        "uses_lagged": False,
        "corners": ["alpha", "beta", "okun_factor", "inflation_target"],
    },
    "balanced_approach_rule": {
        "function": balanced_approach_rule,
        "params": BalancedApproachRuleParameters,
        "extra": {"use_shortfalls_rule": False},
        "uses_real_rate": True,
        "uses_lagged": False,
        "corners": ["alpha", "beta", "inflation_target"],
    },
    "balanced_approach_shortfalls_rule": {
        "function": balanced_approach_rule,
        "params": BalancedApproachRuleParameters,
        "extra": {"use_shortfalls_rule": True},
        "uses_real_rate": True,
        "uses_lagged": False,
        "corners": ["alpha", "beta", "inflation_target"],
    },
    "first_difference_rule": {
        "function": first_difference_rule,
        "params": FirstDifferenceRuleParameters,
        "extra": {},
        "uses_real_rate": False,
        "uses_lagged": True,
        "corners": ["alpha", "inflation_target"],
    },
}

# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def _plain(value):
    """Convert numpy, pandas and float edge values into JSON-safe Python."""
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _compact(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _emit(value, level: int) -> str:
    """Pretty-print dicts; put each case or row of a list on one line."""
    pad = "  " * (level + 1)
    end = "  " * level
    if isinstance(value, dict) and value:
        items = [f"{pad}{json.dumps(k)}: {_emit(value[k], level + 1)}"
                 for k in sorted(value)]
        return "{\n" + ",\n".join(items) + "\n" + end + "}"
    if (isinstance(value, list) and value
            and all(isinstance(v, (dict, list)) for v in value)):
        items = [f"{pad}{_compact(v)}" for v in value]
        return "[\n" + ",\n".join(items) + "\n" + end + "]"
    return _compact(value)


def dumps(value) -> bytes:
    return (_emit(_plain(value), 0) + "\n").encode("utf-8")


def frame_to_split(frame: pd.DataFrame) -> dict:
    """A DataFrame as orient "split" with ISO dates and repr floats."""
    return {
        "columns": [str(c) for c in frame.columns],
        "index": [_plain(i) for i in frame.index],
        "index_name": frame.index.name,
        "data": [[_plain(v) for v in row]
                 for row in frame.itertuples(index=False, name=None)],
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Current-value cases
# ---------------------------------------------------------------------------


def _grid_points(grid: dict):
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        yield dict(zip(keys, values))


def _indicators(point: dict, rule: dict) -> EconomicIndicators:
    lagged_u, lagged_n = point["lagged_unemployment_and_natural_rate"]
    return EconomicIndicators(
        current_fed_rate=point["current_fed_rate"],
        current_inflation_rate=point["inflation"],
        current_unemployment_rate=point["unemployment"],
        natural_unemployment_rate=point["natural_rate"],
        long_term_real_interest_rate=(
            point["long_run_real_rate"] if rule["uses_real_rate"] else None),
        lagged_unemployment_rate=lagged_u if rule["uses_lagged"] else None,
        lagged_natural_unemployment_rate=(
            lagged_n if rule["uses_lagged"] else None),
    )


def _dedupe(grid: dict, rule: dict) -> dict:
    """Drop grid axes a rule never reads, so no case is recorded twice."""
    grid = dict(grid)
    if not rule["uses_real_rate"]:
        grid["long_run_real_rate"] = [None]
    if not rule["uses_lagged"]:
        grid["lagged_unemployment_and_natural_rate"] = [[None, None]]
    return grid


def _run(call):
    try:
        return {"result": call()}
    except Exception as exc:  # 0.2.x's errors are part of the contract
        return {"error": {"type": type(exc).__name__, "message": str(exc)}}


def record_rule(name: str) -> dict:
    rule = RULES[name]
    cases = []
    sets = [("base", None, _dedupe(GRID, rule))]
    sets += [("corner", c, _dedupe(CORNER_GRID, rule)) for c in rule["corners"]]
    for group, corner, grid in sets:
        for point in _grid_points(grid):
            indicators = _indicators(point, rule)
            overrides = dict(rule["extra"], rho=point["rho"],
                             apply_elb=point["apply_elb"])
            if corner is not None:
                overrides[corner] = CORNERS[corner]
            params = rule["params"](**overrides)
            inputs = vars(indicators).copy()
            parameters = vars(params).copy()
            outcome = _run(lambda: rule["function"](indicators, params))
            cases.append({"group": group, "corner": corner,
                          "inputs": inputs, "parameters": parameters,
                          **outcome})
    return {
        "function": f"pyeconomics.{rule['function'].__name__}",
        "pyeconomics": PYECONOMICS_VERSION,
        "case_count": len(cases),
        "cases": cases,
    }


def record_combined() -> dict:
    rule = {"uses_real_rate": True, "uses_lagged": True}
    cases = []
    for point in _grid_points(COMBINED_GRID):
        indicators = _indicators(point, rule)
        arguments = {"inflation_target": 2.0, "rho": point["rho"],
                     "elb": 0.125, "apply_elb": point["apply_elb"]}
        inputs = vars(indicators).copy()
        outcome = _run(lambda: frame_to_split(
            calculate_policy_rule_estimates(indicators, **arguments)))
        cases.append({"inputs": inputs, "arguments": arguments, **outcome})
    return {
        "function": "pyeconomics.calculate_policy_rule_estimates",
        "pyeconomics": PYECONOMICS_VERSION,
        "case_count": len(cases),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Synthetic panel and historical cases
# ---------------------------------------------------------------------------
#
# Every value is an integer expression divided by 100, so the panel is
# exactly reproducible on any IEEE 754 platform (no transcendental calls).
# NROU is observed quarterly and DFII10 starts later and ends earlier than the
# other series, so 0.2.x's forward-fill, drop and cut-off logic all run.

PANEL_START = "2000-01-01"
PANEL_END = "2024-12-01"


def _triangle(t: int, period: int, low: int, high: int) -> float:
    """A triangle wave in hundredths: low at t=0, high at period/2."""
    k = t % period
    distance = k if 2 * k <= period else period - k
    return (low * period + 2 * (high - low) * distance) // period / 100


def _panel() -> dict:
    months = pd.date_range(PANEL_START, PANEL_END, freq="MS")
    t = range(len(months))
    fed = [_triangle(i, 110, 25, 550) for i in t]
    real_mask = (months >= "2003-01-01") & (months <= "2024-06-01")
    quarter_mask = months.month.isin([1, 4, 7, 10])
    return {
        "PCETRIM12M159SFRBDAL": pd.Series(
            [_triangle(i, 96, -50, 650) for i in t], index=months),
        "UNRATE": pd.Series(
            [_triangle(i + 30, 120, 350, 1000) for i in t], index=months),
        "NROU": pd.Series(
            [(480 - (40 * i) // 299) / 100 for i in t],
            index=months)[quarter_mask],
        "DFII10": pd.Series(
            [_triangle(i, 150, -50, 250) for i in t],
            index=months)[real_mask],
        "DFEDTAR": pd.Series(fed, index=months),
        "DFEDTARU": pd.Series(fed, index=months),
    }


PANEL = _panel()


def _stub_fetch_data(series_id: str) -> pd.Series:
    # fetch_historical_fed_funds_rate runs unchanged on the stubbed DFEDTAR
    # and DFEDTARU series, so its splice at 2008-12-15 is characterized too.
    return PANEL[series_id].copy()


def record_historical(function, params_class, extra: dict) -> dict:
    cases = []
    for config in HISTORICAL_CONFIGS:
        arguments = dict(extra, **config)
        if params_class is None:
            outcome = _run(lambda: frame_to_split(
                function(EconomicIndicators(), inflation_target=2.0,
                         rho=config["rho"], elb=0.125,
                         apply_elb=config["apply_elb"])))
        else:
            params = params_class(**arguments)
            arguments = vars(params).copy()
            outcome = _run(lambda: frame_to_split(
                function(EconomicIndicators(), params)))
        cases.append({"arguments": arguments, **outcome})
    return {
        "function": f"pyeconomics.{function.__name__}",
        "pyeconomics": PYECONOMICS_VERSION,
        "panel": "synthetic_panel.json",
        "case_count": len(cases),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Manifest and README
# ---------------------------------------------------------------------------

README = """\
# 0.2.x characterization fixtures

These files record what the published `pyeconomics==0.2.6` returns for a
deterministic grid of explicit inputs. They are written by
`scripts/legacy/record_characterization.py`; do not edit them by hand.

## Layout

| File | Contents |
| ---- | -------- |
| `taylor_rule.json` | `taylor_rule` over the base grid and its parameter corners |
| `balanced_approach_rule.json` | `balanced_approach_rule`, `use_shortfalls_rule=False` |
| `balanced_approach_shortfalls_rule.json` | `balanced_approach_rule`, `use_shortfalls_rule=True` |
| `first_difference_rule.json` | `first_difference_rule` over the base grid and its corners |
| `calculate_policy_rule_estimates.json` | the combined estimates table over a grid subset |
| `synthetic_panel.json` | the synthetic monthly panel the historical functions read |
| `historical_taylor_rule.json` | `historical_taylor_rule` over the panel |
| `historical_balanced_approach_rule.json` | `historical_balanced_approach_rule`, no shortfalls |
| `historical_balanced_approach_shortfalls_rule.json` | the same with shortfalls |
| `historical_first_difference_rule.json` | `historical_first_difference_rule` over the panel |
| `calculate_historical_policy_rates.json` | the combined historical table over the panel |
| `manifest.json` | environment, grid, recorder SHA-256 and a SHA-256 per file |

Each current-value case holds its full `inputs` (the `EconomicIndicators`
fields), its full `parameters` (the parameters dataclass) and either a
`result` or an `error` (exception type and message). A rule that never reads
an indicator (the long-run real rate for the first-difference rule, the
lagged rates for the others) has it left `null`; no case fetches anything.
DataFrames are stored as orient "split": `columns`, `index` (ISO dates for
the historical tables), `index_name` and `data` rows. A missing value is
`null`.

The panel runs monthly from 2000-01 to 2024-12. Every value is an integer
expression divided by 100, so it is exact on any platform. `NROU` is
observed quarterly, and `DFII10` covers 2003-01 to 2024-06 only, so 0.2.x's
forward-fill, drop and cut-off logic all run. `fred_client.fetch_data` is
stubbed per series id; `fetch_historical_fed_funds_rate` runs unchanged on
the stubbed `DFEDTAR` and `DFEDTARU` series.

## Units and rounding

All rates are in percent, as 0.2.x used them (`2.5` means 2.5%). 0.2.x
rounds every rule result to 2 decimal places, and every historical table
with `DataFrame.round(2)`; the fixtures record those rounded values.

## The Phase 3 contract

Phase 3 (ROADMAP 3.6) rebuilds the monetary-policy suite. Its tests load
these fixtures, and the rebuilt rules must match every output here or
document each intentional difference (for example, no longer rounding to
two decimals) next to the test that allows it. 0.2.x's behaviour, errors
included, is the baseline.

## Provenance

Every input is synthetic. The fixtures hold no FRED, Bloomberg or Coin
Metrics value and no credential: the recorder blocks sockets before it
imports 0.2.6 and sets a placeholder `FRED_API_KEY` in its own process.
`manifest.json` records the exact environment. Re-record with

    uv run --no-config --script scripts/legacy/record_characterization.py

and verify with `--check`, which re-records into a temporary directory and
fails on any byte difference. The check is exact on the recording platform
named in the manifest; another OS installs a different set of distributions,
which changes `manifest.json` alone.
"""


def _distributions() -> list:
    names = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        if name:
            names[name.lower().replace("_", "-")] = dist.version
    return [f"{name}=={names[name]}" for name in sorted(names)]


def _recorder_sha256() -> str:
    # Line endings normalized so a CRLF checkout hashes the same.
    source = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    return sha256(source)


def _assert_network_blocked() -> None:
    try:
        socket.create_connection(("api.stlouisfed.org", 443), timeout=1)
    except OSError:
        return
    raise SystemExit("network block failed; refusing to record")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def record(out_dir: Path) -> None:
    _assert_network_blocked()
    if importlib.metadata.version("pyeconomics") != PYECONOMICS_VERSION:
        raise SystemExit(f"expected pyeconomics {PYECONOMICS_VERSION}")
    fred_client.fetch_data = _stub_fetch_data

    files = {f"{name}.json": dumps(record_rule(name)) for name in RULES}
    files["calculate_policy_rule_estimates.json"] = dumps(record_combined())
    files["synthetic_panel.json"] = dumps({
        "description": "Synthetic monthly panel; values are integers / 100.",
        "series": {sid: {"index": [_plain(i) for i in s.index],
                         "values": [_plain(v) for v in s]}
                   for sid, s in PANEL.items()},
    })
    historical = [
        ("historical_taylor_rule", historical_taylor_rule,
         TaylorRuleParameters, {}),
        ("historical_balanced_approach_rule",
         historical_balanced_approach_rule,
         BalancedApproachRuleParameters, {"use_shortfalls_rule": False}),
        ("historical_balanced_approach_shortfalls_rule",
         historical_balanced_approach_rule,
         BalancedApproachRuleParameters, {"use_shortfalls_rule": True}),
        ("historical_first_difference_rule",
         historical_first_difference_rule,
         FirstDifferenceRuleParameters, {}),
        ("calculate_historical_policy_rates",
         calculate_historical_policy_rates, None, {}),
    ]
    for name, function, params_class, extra in historical:
        files[f"{name}.json"] = dumps(
            record_historical(function, params_class, extra))
    files["README.md"] = README.encode("utf-8")

    manifest = {
        "pyeconomics": pyeconomics.__name__ + " " + PYECONOMICS_VERSION,
        "python": sys.version.split()[0],
        "implementation": sys.implementation.name,
        "platform": sys.platform,
        "network": "blocked (socket.socket, create_connection, getaddrinfo)",
        "distributions": _distributions(),
        "grid": {"base": GRID, "corners": CORNERS, "corner_grid": CORNER_GRID,
                 "combined": COMBINED_GRID, "historical": HISTORICAL_CONFIGS,
                 "panel": {"start": PANEL_START, "end": PANEL_END}},
        "recorder_sha256": _recorder_sha256(),
        "files": {name: sha256(data) for name, data in sorted(files.items())},
    }
    files["manifest.json"] = dumps(manifest)

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (out_dir / name).write_bytes(data)


def check() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp)
        record(fresh)
        expected = sorted(p.name for p in fresh.iterdir())
        actual = sorted(p.name for p in FIXTURE_DIR.iterdir()) \
            if FIXTURE_DIR.is_dir() else []
        problems = []
        if expected != actual:
            problems.append(f"file set differs: recorded {expected}, "
                            f"committed {actual}")
        for name in expected:
            committed = FIXTURE_DIR / name
            if committed.is_file() and not filecmp.cmp(
                    fresh / name, committed, shallow=False):
                problems.append(f"{name} differs byte for byte")
    if problems:
        print("characterization check FAILED:", *problems, sep="\n  ")
        return 1
    print(f"characterization check passed: {len(expected)} files identical")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="re-record into a temporary directory and "
                             "compare byte for byte")
    args = parser.parse_args()
    if args.check:
        return check()
    record(FIXTURE_DIR)
    print(f"recorded fixtures into {FIXTURE_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
