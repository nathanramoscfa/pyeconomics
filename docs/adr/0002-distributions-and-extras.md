# ADR-0002: Distributions and extras

- Status: Proposed
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6; §3 Target Architecture; §5 "Dependency licences"

## Context and problem

pyeconomics 1.0 ships one model registry to many surfaces: the Python
library, a CLI, a REST API server, an MCP server, an optional AI
narrative, plotting, data providers and, from Phase 5, a built web app.
Most users want only the library. Pulling FastAPI, an MCP SDK, an LLM
client, Plotly and every provider's client into `pip install pyeconomics`
would make the common install heavy. It would also make it fragile, and
would block the core from running in the browser.

Four facts constrain the packaging:

- **Bloomberg's Python API is not on PyPI.** `blpapi` is absent from PyPI.
  Bloomberg publishes it on its own index, installed with
  `python -m pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi`,
  under a proprietary licence that allows redistribution of copies but no
  modification [S1].
- **A browser core must be pure Python.** Pyodide installs pure-Python
  wheels from PyPI through micropip. A wheel with compiled code must be
  built for its WebAssembly platform [S2]. xlwings Lite runs Python in
  Pyodide inside Excel and installs pure-Python PyPI packages [S3].
- **The build backend is pure-Python only.** `uv_build`, the backend the
  roadmap names (ROADMAP §4 1.2), "currently only supports pure Python
  code" [S4].
- **The standards are settled.** Extras names are normalized (PEP 685,
  Final) [S5]. Development-only dependencies belong in PEP 735 dependency
  groups (Final), which are not published as package metadata [S6].

## Decision drivers

- `pip install pyeconomics` stays small, pure Python and fast.
- Each surface and provider is opt-in, with its dependencies declared in
  one place.
- The core runs in Pyodide and xlwings Lite.
- No proprietary or non-PyPI package appears in published metadata.
- One version number across everything a user installs (ADR-0003).

## Considered options

1. **One `pyeconomics` distribution with extras, plus a separate
   `pyeconomics-app` wheel for the built web app.** Extras select optional
   dependencies. The web app's large built assets ship in their own wheel,
   which `[app]` pulls in.
2. **Many distributions** (`pyeconomics-core`, `pyeconomics-server`,
   `pyeconomics-mcp` and so on). This gives cleaner dependency boundaries,
   but means many PyPI projects, many trusted publishers, many version
   numbers to keep in step, and confusion over which one to install.
3. **One distribution with everything required.** Simple, but the common
   install grows to hundreds of packages, and the core can no longer run in
   the browser.

## Decision outcome

Chosen option: **1**, because it keeps one install name and one version
while making every heavy dependency opt-in. It isolates the web assets, the
only part too large for the main wheel.

**The `pyeconomics` distribution.**

- The core (`core/`, `models/`, `data/`, `cli/`) is pure Python and built
  with `uv_build`.
- Its required runtime dependencies are the minimum the core needs. Each
  must be pure Python, or have wheels for every platform the CI matrix
  covers plus a Pyodide build. All must pass the ADR-0004 licence
  allowlist.

**Extras.** Each extra's dependencies are added by the phase that first
needs them:

| Extra | Pulls in | Phase |
|-------|----------|-------|
| `server` | FastAPI app factory dependencies (local and hosted modes) | 4 |
| `mcp` | MCP server dependencies | 4 |
| `ai` | Optional AI narrative client(s) | 4 |
| `econometrics` | statsmodels-class estimators | 2–3 |
| `plot` | Plotly figure output | 2 |
| one per provider | That provider's client library, if it needs one beyond the core | 3, 6 |
| `app` | The `pyeconomics-app` wheel at the same version | 5 |
| `bloomberg` | The pure-Python side of the Bloomberg provider only; never `blpapi` | 6 |
| `all` | Every extra above except `app` and `bloomberg` | — |

Three rules govern the extras list:

- Extras names follow PEP 685, in lower case.
- An extra exists in `pyproject.toml` from Phase 1 Step 7 as an empty list,
  so the names are stable before their contents arrive.
- `app` and `bloomberg` appear only when their packages exist.

**The `pyeconomics-app` distribution (Phase 5).**

- A wheel holding the built static site that `pyeconomics serve` serves
  (ADR-0006).
- It is versioned and released in lockstep with `pyeconomics`, through the
  same release workflow, and `pyeconomics[app]` pins it to the same
  version.

**Bloomberg.**

- `[bloomberg]` never names `blpapi`, and published metadata never names
  Bloomberg's index or any other non-PyPI URL.
- The docs give Bloomberg's own install command [S1], which the user runs
  on the machine with a Terminal (ADR-0005, class `premium-local`).

**Development dependencies** live in PEP 735 dependency groups (`dev`,
`test`, `docs`) and are never extras.

### Consequences

Good:

- The default install is small, pure Python, and runs in Pyodide and
  xlwings Lite.
- One name, one version and one trusted-publisher pair cover the library.
  The app wheel adds one more PyPI project, released by the same workflow.
- Bloomberg support never puts a proprietary dependency or a private index
  into anyone's resolver.

Bad:

- Every module that uses an optional dependency must import it lazily and
  fail with a clear "install `pyeconomics[x]`" message. Tests must run with
  and without each extra.
- `[all]` can grow large, and a conflict between two extras' dependencies
  breaks it.
- Two PyPI projects (`pyeconomics`, `pyeconomics-app`) need two trusted
  publishers, and they must never drift apart in version.
- A provider whose client is compiled and has no Pyodide build cannot run
  in the browser. Its provider declares that.

### Confirmation

| Check | Built in |
|-------|----------|
| `pyproject.toml` on `uv_build` with the extras skeleton (`server`, `mcp`, `ai`, `econometrics`, `plot`, `all`) and PEP 735 groups | Phase 1 Step 7 |
| Package check: `uv build`, `twine check --strict`, the artifact allowlist and a clean-venv import of the wheel with no extras | Phase 1 Steps 7 and 10 |
| Licence allowlist over the locked runtime set | Phase 1 Step 8 |
| A test that imports `pyeconomics` and runs one model per domain in an environment with no extras installed | Phase 2 (ROADMAP §4 2.7 smoke script) |
| A Pyodide import smoke test of the core wheel | Phase 2 (added to its roadmap by this ADR) |
| Release workflow builds and publishes `pyeconomics-app` at the same version, and `[app]` pins it | Phase 5 (ROADMAP §4 5.5) |
| A metadata check that fails if `blpapi` or any URL appears in `Requires-Dist` | Phase 6 (ROADMAP §4 6.2) |

## More information

- Related: ADR-0004 (licence allowlist), ADR-0005 (data classes the
  providers carry), ADR-0006 (the app wheel's contents), ADR-0010 (Python
  floor).
- Sources:
  - [S1] PyPI has no `blpapi` project (`https://pypi.org/pypi/blpapi/json`
    returns 404). Bloomberg's index at
    https://blpapi.bloomberg.com/repository/releases/python/simple/ serves
    `blpapi` 3.26.9.1 with "License :: Other/Proprietary License" and
    `Requires-Python >=3.10`. Install command from Bloomberg's API library
    page, https://www.bloomberg.com/professional/support/api-library/.
    All accessed 2026-10-05.
  - [S2] Pyodide, "Loading packages": micropip installs pure-Python wheels
    from PyPI, https://pyodide.org/en/stable/usage/loading-packages.html,
    accessed 2026-10-05.
  - [S3] xlwings Lite: Python runs in Pyodide inside Excel, and dependencies
    come from `requirements.txt` (pure-Python PyPI packages or Pyodide
    wheels), https://lite.xlwings.org/ and
    https://lite.xlwings.org/dependencies, accessed 2026-10-05.
  - [S4] uv build backend: "currently only supports pure Python code"; uv
    and uv_build 0.12.23 (2026-10-03),
    https://docs.astral.sh/uv/concepts/build-backend/, accessed 2026-10-05.
  - [S5] PEP 685, Comparison of extra names for optional distribution
    dependencies (Final), https://peps.python.org/pep-0685/, accessed
    2026-10-05.
  - [S6] PEP 735, Dependency Groups in pyproject.toml (Final),
    https://peps.python.org/pep-0735/, accessed 2026-10-05.
