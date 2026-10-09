# ADR-0008: Numerical conventions

- Status: Accepted
- Date: 2026-10-09
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 2.1–2.4; §5 "Model quality & governance"

## Context and problem

Phase 2 builds the model registry and the first 32 catalog entries, and
every later surface is generated from them: the CLI, REST API and MCP
server (Phase 4) and the web pages (Phase 5). Each of those surfaces must
return the same bytes for the same inputs (ROADMAP §5, "Parity"). That is
only possible if every model encodes the same answer to a set of
questions: is 5% written `5` or `0.05`? Which unit is a field in, and how
large may it be? How does a rate compound, and how are days counted? How
close is close enough in a test? Where does randomness come from? What
happens to NaN, to an undefined ratio, to an equation with no root or
several? How are numbers written to canonical JSON? Which exceptions and
warnings does a caller see? Which libraries may the core depend on?

Without one answer, a model that takes percent sits beside one that takes
decimals, golden tests disagree about tolerance, two surfaces format the
same float differently, and an IRR silently picks a different root in
each implementation. Once 1.0.0 ships, each of these becomes public API
that only a major release can change (ADR-0003). ADR-0008 was reserved for
these conventions in Phase 1 (ROADMAP §4 2.1).

The facts the decisions rest on:

- **pandas 3.0** (released 2026-01-21) makes Copy-on-Write the only mode
  and enables a dedicated `str` string dtype by default (backed by
  PyArrow when installed, otherwise by Python objects). It removed the
  `M`, `Q` and `Y` offset aliases in favour of `ME`, `QE` and `YE`, and it
  infers a datetime resolution from the input [S1]. Strings parse to
  microseconds unless they carry nanoseconds, `datetime` objects keep
  microseconds, and `np.datetime64` values keep their unit, capped to the
  range from seconds to nanoseconds [S1]. Checked with pandas 3.0.6 on
  2026-10-09: `date` objects and `datetime64[D]` values become
  `datetime64[s]`. A frame's resolution therefore depends on how it was
  built. pandas 3 also imports and exports data through the Arrow
  PyCapsule interface (`__arrow_c_stream__`, `DataFrame.from_arrow`) [S1].
- **NumPy's random streams** are guaranteed stable across versions only
  for a bit generator's `bytes`, `integers` and `random` methods. A
  `Generator`'s distribution methods may change their streams in a
  feature release (`X.Y`), never in a patch release (NEP 19, Final) [S2].
- **SciPy's `brentq`** defaults to `xtol=2e-12`, `rtol=4*eps` (it refuses
  anything smaller) and `maxiter=100`. Its root satisfies
  `np.isclose(x, x0, atol=xtol, rtol=rtol)`, and with `disp=True` it
  raises `RuntimeError` when it does not converge (SciPy 1.18.0) [S3].
- **RFC 8785, the JSON Canonicalization Scheme** (2020), serializes
  numbers as ECMAScript does: the shortest decimal that round-trips an
  IEEE 754 double. It sorts object keys by their UTF-16 code units,
  encodes the result as UTF-8, and ends with an error on NaN or infinity.
  It recommends that integers beyond a double's precision travel as
  strings [S4].
- **Day counts have authoritative definitions.** The 2006 ISDA
  Definitions define day count fractions in Section 4.16 [S5]. ICMA Rule
  251 defines Actual/Actual (ICMA) for bonds [S6]. QuantLib 1.43 documents
  the US 30/360 end-of-month rules in its `Thirty360::USA` convention [S7].
- **`holidays` 0.106** (2026-08-17) is MIT-licensed, pure Python (a
  `py3-none-any` wheel), and requires only `python-dateutil` [S8].
- **Pyodide 314.0.7** runs Python 3.14.2. Its lockfile bundles numpy
  2.4.6, scipy 1.18.0, pandas 3.0.2, pydantic 2.12.5 and pydantic-core
  2.41.5 [S9]. The newest PyPI releases on 2026-10-09 were numpy 2.5.3
  (2026-09-06), scipy 1.18.1 (2026-08-21), pandas 3.0.6 (2026-09-17) and
  pydantic 2.14.0 (2026-10-08) [S10]. A requirement above Pyodide's
  version cannot install there.
- **The licence check** (`scripts/checks/licences.py`, ADR-0004) fails
  numpy, scipy, pandas and python-dateutil on their metadata alone. Their
  licence files are permissive, so each carries a reviewed entry in
  `scripts/checks/licence_exceptions.toml`, which the maintainer approved
  in Phase 2 Step 1's pull request.

## Decision drivers

- **Parity.** A number means the same thing, in the same unit and the
  same bytes, in every model and on every surface.
- **Correctness.** Every convention follows a cited definition exactly,
  and every output carries a stated tolerance.
- **Reproducibility.** The same inputs and seed give the same outputs, and
  the manifest records what could change them.
- **Safety.** Every input is finite and bounded, which protects
  correctness and is what Phase 4's request limits build on.
- **Portability and licence.** The core runs in Pyodide (ADR-0002), on
  the Python floor ADR-0010 sets, with permissive dependencies
  (ADR-0004).
- **Mechanical rules.** A later step or a contributor applies each rule
  without re-arguing it.

## Considered options

1. **Decimals with typed units, enforced in `pyeconomics.core` on
   pydantic, NumPy, SciPy and pandas.** Every convention below lives in
   one package, which the registry's validation and the schemas build on.
2. **Percent in the public API.** It matches how FRED and most people
   quote rates. But every formula then divides by 100, and a model that
   forgets to is wrong by a factor of 100 without any error. Mixing the
   two is the most common unit bug in financial code. Rejected: percent
   stays at the display and data boundaries.
3. **Exact decimal arithmetic (`decimal.Decimal`) throughout.** It is
   exact for money. But it is slow, and NumPy, SciPy and pandas do not
   support it, so every statistical and numerical model would need its
   own implementation. Rejected: binary floats, with tolerances stated per
   output.
4. **A pure-Python core without NumPy, SciPy or pandas.** It would install
   anywhere. But root finding, linear algebra, distributions and
   time-series handling would have to be rewritten and verified from
   scratch. All three libraries have Pyodide builds [S9]. Rejected.
5. **Conventions chosen per model, recorded on its card.** No parity, and
   no way for a generated surface to treat fields uniformly. Rejected.

## Decision outcome

Chosen option: **1**. It gives every question above one answer, in code
that `registry.validate()`, the schemas and the verification harness can
check. Its dependencies run in Pyodide and pass the licence check, with
reviewed exceptions. The fourteen decisions below are rules a later step
follows as written.

### 1. Decimals

- Rates, returns, yields, spreads, volatilities and probabilities are
  decimals in every API: `0.05` is 5%.
- Percent and basis points exist only in display formatting and at the
  data boundary, where a source such as FRED publishes percent.
- The converters in `pyeconomics.core.rates` are the only ones:
  `percent_to_decimal`, `decimal_to_percent`, `basis_points_to_decimal`
  and `decimal_to_basis_points`. Nothing else multiplies or divides by
  100 or 10,000 to change a rate's scale.
- Display goes through `format_percent` and `format_basis_points`.

### 2. Units

- Every numeric input and output field declares one unit kind from a
  closed vocabulary in `pyeconomics.core.units`:
  - `rate`, `return`, `money`, `years`;
  - `days`, `periods`, `count`, `ratio`;
  - `probability`, `volatility`, `correlation`, `index_level`, `date`.
- A field declares its kind with the `Annotated` markers `Rate`,
  `Return`, `Money`, `Years`, `Days`, `Periods`, `Count`, `Ratio`,
  `Probability`, `Volatility`, `Correlation`, `IndexLevel` and
  `DateValue`.
- The kind is exported to the field's JSON Schema as `x-unit`.
- `days` and `count` are whole numbers. `periods` may be fractional (a
  bond priced between coupon dates).
- A `money` field takes its currency (ISO 4217) from an input field. It
  may instead be currency-agnostic when the formula is linear in money and
  all its money fields share one currency.
- Adding a unit kind is a reviewed code change in `units.py`, not an ADR
  change.

### 3. Bounds

- Every numeric field has finite lower and upper bounds, and every array
  and string a maximum length.
- A model may narrow the defaults below. It may widen them only with a
  recorded reason.
- Bounds protect correctness, and Phase 4's request limits build on them.

| Unit kind | Default bounds |
|-----------|----------------|
| `rate` | −0.99 to 10 |
| `return` | −1 to 100 |
| `money` | −10¹⁵ to 10¹⁵ |
| `years` | 0 to 200 |
| `days` | 0 to 73,050 |
| `periods` | 0 to 100,000 |
| `count` | 0 to 10⁹ |
| `ratio` | −10⁶ to 10⁶ |
| `probability` | 0 to 1 |
| `volatility` | above 0, to 10 |
| `correlation` | −1 to 1 |
| `index_level` | 0 to 10⁹ |
| `date` | 1900-01-01 to 2200-12-31 |
| array | at most 100,000 items |
| string | at most 256 characters |

Ends are inclusive except volatility's lower end. The table lives in
`pyeconomics.core.units` as `DEFAULT_BOUNDS`, `DEFAULT_DATE_BOUNDS`,
`MAX_ARRAY_LENGTH` and `MAX_STRING_LENGTH`.

### 4. Frequency and compounding

- A `Frequency` enum (annual, semiannual, quarterly, monthly, weekly,
  daily) carries its periods per year: 1, 2, 4, 12, 52 and 365 (daily is
  calendar-daily).
- A `Compounding` enum has three members: simple, periodic and
  continuous.
- `pyeconomics.core.compounding` converts among nominal, effective annual
  and continuous rates and discount factors:
  - accumulation factors: `1 + rt` (simple), `(1 + r/m)^(mt)` (periodic)
    and `e^(rt)` (continuous);
  - their reciprocals, the discount factors;
  - their inverse, the implied rate;
  - the effective annual rate;
  - conversion between any two compoundings over a stated horizon.
- Periodic compounding requires a frequency, and the other two refuse
  one.
- Annualizing a return series takes an explicit `periods_per_year` (252
  trading days, say), never one guessed from the data.
- Time-indexed data use pandas 3's `ME`, `QE`, `YE`, `W` and `B`
  aliases. `Frequency.pandas_alias` maps each frequency to its period-end
  alias.

### 5. Day counts and calendars

Step 2 builds these.

- **`DayCount` members.** Each is defined by its source, cited by section
  and never quoted:
  - `THIRTY_E_360`, `ACT_360`, `ACT_365_FIXED` and `ACT_ACT_ISDA`, by the
    2006 ISDA Definitions §4.16 [S5];
  - `ACT_ACT_ICMA`, by ICMA Rule 251 [S6];
  - `THIRTY_360_US`, by the US 30/360 end-of-month rules as QuantLib's
    `Thirty360::USA` applies them [S7].
- **`BusinessDayConvention` members:** `UNADJUSTED`, `FOLLOWING`,
  `MODIFIED_FOLLOWING`, `PRECEDING` and `MODIFIED_PRECEDING`.
- **Calendars** come from the `holidays` package (MIT, pure Python) [S8].
  Each sits behind a stable calendar id that never changes once released.
- **Schedules** are unadjusted unless an input asks otherwise.

### 6. Tolerance

- An output's tolerance is an absolute and a relative bound with
  `math.isclose` semantics [S11]. Two values agree when
  `|a − b| ≤ max(rel_tol × max(|a|, |b|), abs_tol)`.
- NaN never agrees with anything, and dates and undefined (`None`)
  outputs compare by equality.
- Defaults per unit kind live in `pyeconomics.core.tolerance`:

| Unit kinds | Absolute | Relative |
|------------|----------|----------|
| `rate`, `return`, `ratio`, `probability`, `volatility`, `correlation` | 10⁻¹² | 10⁻⁹ |
| `money`, `years`, `index_level`, `periods` | 10⁻⁹ | 10⁻⁹ |
| `count`, `days`, `date` | exact | exact |

- A model may declare its own tolerance for an output.
- A golden case may loosen its tolerance to its source's published
  precision, and records why.

### 7. Randomness

- Every stochastic model takes an integer `seed` input from 0 to
  2⁵³ − 1, the largest integer canonical JSON carries exactly (decision
  12).
- Its documented default is 0 unless the model documents another.
- It draws only from `pyeconomics.core.random.generator(seed)`, which
  returns `numpy.random.Generator(PCG64(seed))`. There is no global or
  unseeded state.
- The manifest records the seed, the bit generator and NumPy's version,
  because NumPy does not promise identical `Generator` streams across
  feature releases [S2].

### 8. Arrays and tabular data

- A field is scalar unless declared with an array type and a maximum
  length.
- Array fields accept lists, tuples, NumPy arrays and objects exposing
  the Arrow PyCapsule stream interface (pandas 3, Polars, pyarrow) [S1],
  without a copy where the memory layout allows.
- `run_batch` (Step 4) evaluates a scalar model over the rows of a table.
- Results default to pandas.
- **Polars and pyarrow are never dependencies, not even through an
  extra.** A caller who asks for a Polars or Arrow result already has the
  library. Conversions import it lazily, and raise
  `MissingOptionalDependencyError` naming the package when it is absent.

### 9. pandas 3 semantics

The core is written for pandas 3's semantics [S1]:

- Copy-on-Write: no code relies on a view writing through to its parent.
- The default `str` string dtype.
- The `ME`, `QE` and `YE` aliases.
- **One explicit datetime resolution: microseconds, `datetime64[us]`.**
  pandas 3 infers microseconds from strings and `datetime` objects but
  seconds from `date` objects, so every datetime index or column the core
  builds or returns is converted to `us` explicitly (`as_unit("us")`).
  Microseconds match the precision of Python's `datetime`. They cover
  every date in decision 3's bounds, and far beyond: nanoseconds stop at
  2262-04-11.

### 10. Non-finite and undefined results

- Inputs reject NaN and infinity. The unit markers enforce it.
- NaN and infinity never reach a `Result` or canonical JSON.
- **One rule decides between an error and a null:**
  - When valid inputs leave the model's result as a whole undefined,
    `compute` raises `DomainError`. Examples: a Gordon growth value with a
    required return not above growth, or a singular covariance matrix.
  - When one output is undefined while the others are meaningful, that
    output is `None` (JSON `null`), with a warning code saying why.
    Examples: an IRR with no sign change, a ratio with a zero denominator,
    or a Sharpe ratio with zero volatility.

### 11. Root finding

`pyeconomics.core.numerics.find_root` uses bracketed Brent's method
(`scipy.optimize.brentq`) [S3] under one policy:

- **Tolerances:** `xtol = 2×10⁻¹²`, `rtol = 4ε` (8.88×10⁻¹⁶) and at most
  100 iterations, SciPy's own defaults.
- **Scan:** the bracket is scanned at 64 evenly spaced points for sign
  changes.
- **Expansion:** with no sign change, the end whose value is smaller in
  magnitude moves outward by 1.6 times the bracket's width. It moves at
  most 50 times, and never past the limits the caller gives, usually the
  bounds of the input being solved for. With no limits, the bracket does
  not expand.
- **No root:** no sign change raises `ConvergenceError`. So does failing
  to converge. A model whose output is then undefined returns a
  documented `None` with a warning instead (decision 10).
- **Several roots:** the smallest root is used, with a `several_roots`
  warning. A model with a different convention (an IRR nearest a guess)
  chooses for itself from `bracket_roots` and documents its choice.
- The scan sees sign changes only. A model that must not miss a root
  that touches zero without crossing it chooses its own grid.

### 12. Canonical JSON numbers

Canonical JSON follows RFC 8785 (JCS) [S4]:

- UTF-8, with object keys sorted by their UTF-16 code units.
- Numbers in ECMAScript's shortest round-trip form.
- No NaN or infinity.
- Integers exact within ±2⁵³; a larger integer cannot be serialized.
- Dates as ISO 8601 strings.

Step 4 implements it, and the cross-surface parity tests compare these
bytes.

### 13. Errors and warnings

`pyeconomics.core.errors` and `pyeconomics.core.warnings` hold the
taxonomy.

- **`PyeconomicsError` is the base.** Each subclass also derives from the
  built-in exception a caller would expect:
  - `InputError` (also a `ValueError`) wraps pydantic's validation error;
  - `DomainError` (`ValueError`): valid inputs with no defined result;
  - `ConvergenceError` (`RuntimeError`);
  - `ModelNotFoundError` (`LookupError`);
  - `RegistryError`;
  - `MissingOptionalDependencyError` (`ImportError`) names the extra or
    package to install.
- **`PyeconomicsWarning` is a `UserWarning`.**
  - `ModelWarning` carries a stable snake_case `code`, is issued through
    `pyeconomics.core.warn()`, and is carried in a `Result`.
  - `PyeconomicsDeprecationWarning` is also a `FutureWarning`, so it is
    visible by default. Issued through `pyeconomics.core.deprecated()`, it
    names the replacement and the removing release (ADR-0003).

### 14. Runtime dependencies and Pyodide

- The required runtime set is pydantic, NumPy, SciPy and pandas, and
  `holidays` from Step 2.
- Each lower bound is no higher than the version the current Pyodide
  bundles. For Pyodide 314.0.7 [S9] that means `numpy>=2.4`,
  `scipy>=1.18`, `pandas>=3.0` and `pydantic>=2.12`.
- None has an upper bound. `uv.lock` pins the newest releases for CI.
- The Python floor still follows ADR-0010.
- Each passes `pip-audit` and the licence check, or carries a reviewed
  exception.
- A CI job installs the wheel into Pyodide with these packages from
  Pyodide's own index, and runs `scripts/smoke.py` there.

### Consequences

Good:

- A rate, a unit, a bound, a tolerance and a seed mean the same thing in
  every model, so the generated surfaces of Phases 4 and 5 can treat
  fields uniformly and return identical bytes.
- Percent-versus-decimal errors are confined to four functions at the
  boundary. A model's bounds, narrowed to its domain, catch many of the
  rest: a yield capped at 1.0 refuses a `5` meant as 5%.
- Every result is reproducible from its manifest, randomness included.
- The core runs in Pyodide and in xlwings Lite on the same code.

Bad:

- Users who think in percent must convert at the boundary. The CLI and web
  forms of Phases 4 and 5 must display percent while sending decimals.
- Binary floats mean an output is right only to its tolerance. Money
  totals are not exact to the cent, and a model that needs exact money
  arithmetic must say so on its card.
- The four floors track Pyodide, not PyPI, so a feature added to NumPy
  after 2.4 cannot be used until Pyodide bundles it.
- Four permissive dependencies need reviewed licence exceptions, and each
  must be reviewed again when its metadata changes.
- A NumPy feature release may change a stochastic model's draws for the
  same seed. The manifest records the version, but such a change is a
  model version bump under ADR-0003.

### Confirmation

| Decision | Check | Built in |
|----------|-------|----------|
| 1 Decimals | `core/rates.py` converters and formatters, unit and property tests | Phase 2 Step 1 |
| 1 Decimals | Golden cases and examples state every rate as a decimal, against cited values | Phase 2 Steps 5–12 |
| 2 Units | The unit markers emit `x-unit`; a test reads it from a JSON Schema | Phase 2 Step 1 |
| 2 Units | `registry.validate()` rejects a numeric field with no unit; schema export carries `x-unit` | Phase 2 Steps 3 and 4 |
| 3 Bounds | A test pins `DEFAULT_BOUNDS` and the length limits | Phase 2 Step 1 |
| 3 Bounds | `registry.validate()` rejects an unbounded numeric field, array or string | Phase 2 Step 3 |
| 4 Compounding | `core/compounding.py` closed-form tests; property tests (round trips, the effective annual rate rising with frequency, discount factors falling with maturity) | Phase 2 Step 1 |
| 5 Day counts | Six day counts, schedules and calendars checked against QuantLib | Phase 2 Step 2 |
| 6 Tolerance | `core/tolerance.py` tests against `math.isclose`; the golden harness applies each case's tolerance | Phase 2 Steps 1 and 5 |
| 7 Randomness | Generator determinism and independence tests; the manifest records the seed, bit generator and NumPy version; the `model-purity` semgrep rule forbids unseeded randomness in models | Phase 2 Steps 1, 3 and 4 |
| 8 Arrays | `run_batch`, the PyCapsule input path, and conversions that raise `MissingOptionalDependencyError` | Phase 2 Step 4 |
| 9 pandas 3 | `Frequency.pandas_alias` tests against pandas 3; results carry `datetime64[us]` | Phase 2 Steps 1 and 4 |
| 10 Non-finite | The unit markers reject NaN and infinity; canonical JSON refuses them | Phase 2 Steps 1 and 4 |
| 11 Root finding | `core/numerics.py` tests: a known root, no root, several roots, expansion, non-convergence | Phase 2 Step 1 |
| 12 Canonical JSON | RFC 8785 test vectors | Phase 2 Step 4 |
| 13 Errors and warnings | Taxonomy tests, including a fresh interpreter showing `PyeconomicsDeprecationWarning` under the default filters | Phase 2 Step 1 |
| 14 Dependencies | The `licences`, `pip-audit` and `lock-index` hooks; the `pyodide` CI job runs `scripts/smoke.py` in Pyodide 314.0.7 | Phase 1 Step 8; Phase 2 Step 1 |
| 14 Dependencies | Each release step re-checks the floors against the current Pyodide | Phase 2 Steps 13 and 14 |

## More information

- Related: ADR-0002 (pure-Python core, Pyodide smoke test), ADR-0003
  (deprecation warning, model versions), ADR-0004 (licence allowlist and
  exceptions), ADR-0010 (Python floor); ROADMAP §4 2.1–2.4 and §5 "Model
  quality & governance".
- The maintainer accepted the fourteen decisions, with the values in this
  record, in Phase 2 Step 1's pull request on 2026-10-09.
- Amended before merge, 2026-10-09, by the maintainer: `periods` take the
  money and years tolerance (10⁻⁹ absolute and relative) instead of an
  exact one, because a number of periods may be fractional (decision 2).
- Sources, all accessed 2026-10-09:
  - [S1] pandas 3.0.0 release notes ("Copy-on-Write", "Dedicated string
    data type", "Datetime resolution inference", the renamed offset
    aliases and the Arrow PyCapsule interface),
    https://pandas.pydata.org/docs/whatsnew/v3.0.0.html. The `date` and
    `datetime64[D]` behaviour was checked with pandas 3.0.6.
  - [S2] NEP 19, Random number generator policy (Final),
    https://numpy.org/neps/nep-0019-rng-policy.html.
  - [S3] SciPy 1.18.0, `scipy.optimize.brentq`,
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html.
  - [S4] RFC 8785, JSON Canonicalization Scheme (JCS), §3.1, §3.2.2.3,
    §3.2.3 and §3.2.4, https://www.rfc-editor.org/rfc/rfc8785.
  - [S5] ISDA, 2006 ISDA Definitions, Section 4.16 "Day Count Fraction"
    (the published blackline against the 2000 Definitions:
    https://www.isda.org/a/smMDE/Blackline-2000-v-2006-ISDA-Definitions.pdf).
  - [S6] ICMA Secondary Market Rules & Recommendations, Rule 251
    (Actual/Actual (ICMA) at Rule 251.1(iii)), as ICMA's Primary Market
    Handbook, Appendix A5 (March 2022), describes it,
    https://www.icmagroup.org/assets/documents/ICMA-PMH-Appendix-A5-March-2022.pdf.
  - [S7] QuantLib 1.43 reference, `Thirty360` conventions,
    https://www.quantlib.org/reference/class_quant_lib_1_1_thirty360.html.
  - [S8] PyPI, `holidays` 0.106 (MIT, `py3-none-any`,
    `python-dateutil>=2.9.0.post0`), https://pypi.org/pypi/holidays/json.
  - [S9] Pyodide 314.0.7 lockfile,
    https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json
    (Python 3.14.2; numpy 2.4.6, scipy 1.18.0, pandas 3.0.2, pydantic
    2.12.5, pydantic-core 2.41.5); cross-build environment metadata,
    https://pyodide.github.io/pyodide/api/v2/pyodide-cross-build-environments.json.
  - [S10] PyPI JSON for `numpy`, `scipy`, `pandas` and `pydantic`,
    https://pypi.org/pypi/<name>/json.
  - [S11] Python 3 documentation, `math.isclose`,
    https://docs.python.org/3/library/math.html#math.isclose.
