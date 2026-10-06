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
