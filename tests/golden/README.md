# Golden cases

A golden case is a published value a model must reproduce: inputs, the outputs a
cited source gives for them, and a tolerance. Every catalog model has one file of
them, and the harness in this directory refuses a model that lacks one, or whose
file breaks a rule below. The rules are ROADMAP §5 "Model quality & governance":
at least three cited cases including an edge case, each with a tolerance.

```sh
uv run pytest tests/golden            # the harness, over the installed registry
uv run pytest tests/golden -k harness # the harness's own tests, over toy models
```

## Where a file goes

One TOML file per model, named by its id and placed in its domain's directory:

| Model id                   | Golden file                              |
| -------------------------- | ---------------------------------------- |
| `fixed_income.duration`    | `tests/golden/fixed_income/duration.toml`  |
| `equity.dcf.gordon_growth` | `tests/golden/equity/dcf_gordon_growth.toml` |

`scripts/new_model.py <id>` creates a skeleton in the right place. A file in the
wrong place, two files for one model, and a file naming a model that is not
registered all fail.

Files are read with `tomllib` and nothing in them is ever evaluated. A key the
format does not define is an error, so a typo cannot silently drop a case.

## The format

```toml
# tests/golden/fixed_income/zero_coupon_price.toml
model = "fixed_income.zero_coupon_price"
# min_cases_reason = "Why fewer than three cases, or no edge case, can be right."

[[sources]]
key = "agency_table"
kind = "official"                          # certified | official | paper | textbook | identity
citation = "Example Agency (2024). Example price table. Example Agency."
url = "https://example.com/price-table"    # or doi = "10.xxxx/..." or isbn = "..."

[[sources]]
key = "textbook_example"
kind = "textbook"
citation = "Example Author (2020). Example Textbook, 3rd ed. Example Press."
isbn = "9780000000000"
published_digits = 2                       # the value is printed to 2 decimal places
# recomputed_with = "numpy_financial.pv"   # or: the independent method that recomputed it

[[sources]]
key = "closed_form"
kind = "identity"
citation = "P = F / (1 + y)^T, with y = 0, gives P = F."

[[cases]]
id = "five_percent_ten_years"
source = "agency_table"
locator = "Table 2, row 4"                 # a page, table, section or equation
edge = false
inputs = { face_value = 100, rate = 0.05, years = 10 }
expected = { price = 61.39132535 }
note = "Optional: anything a reviewer should know."

[[cases]]
id = "textbook_price"
source = "textbook_example"
locator = "Example 4.2"
edge = false
inputs = { face_value = 100, rate = 0.04, years = 5 }
expected = { price = 82.19 }
tolerance = { price = { abs = 0.005 } }    # half a unit of the 2 published digits

[[cases]]
id = "zero_rate"
source = "closed_form"                      # an identity needs no locator
edge = true
inputs = { face_value = 100, rate = 0.0, years = 30 }
expected = { price = 100.0 }
```

### Top level

| Key                | Required | Meaning                                                           |
| ------------------ | -------- | ----------------------------------------------------------------- |
| `model`            | yes      | The model's id.                                                   |
| `min_cases_reason` | no       | Why fewer than three cases, or no edge case, is right for it.     |
| `[[sources]]`      | yes      | The sources the cases cite.                                       |
| `[[cases]]`        | yes      | The cases.                                                        |

### `[[sources]]`

| Key                | Required                  | Meaning                                                    |
| ------------------ | ------------------------- | ---------------------------------------------------------- |
| `key`              | yes                       | A unique label the cases cite.                             |
| `kind`             | yes                       | `certified`, `official`, `paper`, `textbook` or `identity`. |
| `citation`         | yes                       | Authors, year, title, publisher. Your own words.           |
| `url`, `doi`, `isbn` | one, unless `identity`  | Where to find it.                                          |
| `recomputed_with`  | textbook, one of these two | The independent method that reproduced the value.        |
| `published_digits` | textbook, one of these two | Decimal places the value is printed to.                   |

| Kind        | Use it for                                                                         |
| ----------- | ---------------------------------------------------------------------------------- |
| `certified` | Certified reference values (NIST StRD).                                            |
| `official`  | A government or standard-setter's published figures (US Treasury, Federal Reserve, BIS, ISDA). |
| `paper`     | A peer-reviewed paper. The *Financial Analysts Journal* counts.                    |
| `textbook`  | A value from a textbook, recomputed independently or quoted at its precision.      |
| `identity`  | A closed-form identity, such as put-call parity or a zero-rate limit.              |

### `[[cases]]`

| Key             | Required                | Meaning                                                                   |
| --------------- | ----------------------- | ------------------------------------------------------------------------- |
| `id`            | yes                     | A unique snake_case name; it names the test.                              |
| `source`        | yes                     | A source `key`.                                                           |
| `locator`       | unless the source is an `identity` | Page, table, section or equation in the source.                |
| `edge`          | yes                     | `true` for an edge case (below).                                          |
| `inputs`        | yes                     | An inline table, passed to `pyeconomics.run`. A model with several calculations needs `calculation`. |
| `expected`      | one of these two        | Output field → value. A list for an array output, a TOML date for a date. |
| `expected_none` | one of these two        | Output fields that must be `None` (undefined, with a warning).            |
| `tolerance`     | no                      | Output field → `{ abs = ..., rel = ... }`.                                |
| `note`          | no                      | Context for a reviewer.                                                   |

An output the case does not list is not checked. A field that is not an output of
the case's calculation (for a family of calculations, the one `calculation`
selects) fails.

## Tolerance

Two values agree when `abs(actual - expected) <= max(rel * max(abs(actual),
abs(expected)), abs)`, as `math.isclose` has it (ADR-0008 decision 6). With no
`tolerance` for a field, the default for its unit applies:

| Unit kinds                                                           | `abs`  | `rel`  |
| -------------------------------------------------------------------- | ------ | ------ |
| `rate`, `return`, `ratio`, `probability`, `volatility`, `correlation` | 1e-12  | 1e-9   |
| `money`, `years`, `index_level`, `periods`                           | 1e-9   | 1e-9   |
| `count`, `days`, `date`, and fields with no unit                     | exact  | exact  |

A `tolerance` entry replaces the default for that field; an omitted `abs` or `rel`
is zero. Dates, text and booleans compare exactly. An array compares item by item.

**A textbook value is quoted at its published precision or recomputed.** A source
that gives `published_digits` lets a case loosen its tolerance to half a unit in
the last digit (`abs = 0.005` for two decimals), and no tighter: a case that claims
more precision than the book printed fails. A source that gives `recomputed_with`
names the independent method that reproduced the value, so the default tolerance
stands.

## Edge cases

At least one case per file is an edge case (`edge = true`), drawn from the
categories that apply to the model:

- **zero and negative rates**: a rate of exactly zero, and a negative one;
- **very long maturities**: 50 years or more;
- **extreme volatilities**: 2.0 (200%) or more;
- **degenerate inputs**: a single cash flow, zero variance, the smallest valid
  sample.

`min_cases_reason` records why a model has fewer than three cases or no edge case
(an identity with one published value, say). It is a sentence a reviewer can
disagree with, not a way past the check.

## What a source may be

The Citation rule (Phase 2 roadmap, Overview): a case cites an independent source
with a locator: certified or official values, a peer-reviewed paper, a textbook
value recomputed or quoted at its precision, or a closed-form identity.

- **Never the CFA Program curriculum**: its readings, learning outcome statements,
  practice problems, mock exams and worked examples. `test_sources.py` rejects them,
  and a `cfainstitute.org` link other than the *Financial Analysts Journal*'s.
- **Numbers and formulas only, in your own words.** Do not copy a source's prose.
- **No dataset.** A file holds the handful of values a case needs, each cited. No
  licensed data enters the repository (ROADMAP §5 "Data terms").
- List every new source in the pull request body.

## What the harness checks

| Rule                                                                              | Where                    |
| --------------------------------------------------------------------------------- | ------------------------ |
| A registered model has a file; a file names a registered model, in the right place | `audit`                  |
| No unknown key; every value has its type                                          | `load_golden`            |
| A case cites a defined source, and has a locator unless the source is an identity | `file_problems`          |
| A source has a link (unless an identity); a textbook source has its method or digits | `file_problems`        |
| At least three cases and an edge case, or a `min_cases_reason`                    | `file_problems`          |
| A textbook case's tolerance is no tighter than its published digits               | `file_problems`          |
| An expected field is an output of the case's calculation                          | `file_problems`, `run_case` |
| No `TODO` placeholder left by the scaffold                                        | `file_problems`          |
| The model's outputs match within tolerance                                        | `run_case`               |
| No source or reference cites the CFA Program curriculum                           | `test_sources.py`        |

`test_harness.py` gives each rule a toy model and a file that breaks it.
