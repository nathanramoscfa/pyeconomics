# ADR-0001: Product boundaries

- Status: Proposed
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6; §1 "Where pyeconomics fits"; §6 Out of Scope

## Context and problem

pyeconomics 1.0 aims to be the reference open-source platform for economic
and financial models: every CFA Program formula family first, then the
wider economics, econometrics, risk and quant canon (ROADMAP §1). An
ambition that broad needs a fence. Without one, the project drifts into
neighbouring products that others already do well, or that carry legal
risk. Examples: a data platform, a trading system, an exam-prep service, a
licensed-data reseller.

The neighbours, as of 2026-10-05:

- **OpenBB Open Data Platform.** It moves data across providers, and one
  spec drives Python, CLI, REST and MCP. Its v5.0.0 (2026-09-30) moved from
  AGPL-3.0-only to Apache-2.0 [S1].
  - The project is now stewarded by OpenBQ, a non-profit open-source
    foundation [S2].
  - In August 2026 OpenBB wrote that it "couldn't find the product-market
    fit needed to build a sustainable business around this vision within
    the time we had" [S3].
  - It has few models: no bond or derivative pricing, no curriculum
    breadth (ROADMAP §1).
- **QuantEcon.** It teaches economic theory. The QuantEcon.py library is
  MIT [S4], and the lectures are CC BY-SA 4.0 [S5]. Share-alike means
  adapted lecture text would have to carry the same licence.
- **FinanceToolkit.** It computes 500+ ratio, valuation and risk methods
  over tickers. MIT [S6].
- **Pricing libraries with incompatible licences.**
  - FinancePy is GPL-3.0-or-later [S7].
  - rateslib is "source-available non-commercial" and states it "is not
    open source" [S8].
  - QuantLib is BSD-3-Clause [S9].
- **The maintainer's own portfolio system.** A separate, private project
  that may want to call pyeconomics' models.

## Decision drivers

- Correct before broad: scope must not outrun the model definition of
  done (ROADMAP §5 "Model quality & governance").
- Complement strong neighbours rather than rebuild them, because one
  maintainer cannot out-build a funded data platform.
- Keep the project a publisher of impersonal tools, never an adviser
  (ROADMAP §5 "Legal & brand guardrails").
- Keep the licence clean for a permissive core and a hosted service
  (ADR-0004).

## Considered options

1. **The model layer.** pyeconomics computes. Data platforms feed it, and
   teaching sites explain the theory it implements. It integrates with
   both and depends on neither.
2. **A full-stack finance platform** (data, models, portfolio, trading).
   It competes with OpenBB on data and with commercial terminals on
   workflow. It pulls in adviser regulation, and it is beyond one
   maintainer.
3. **A teaching platform** (lectures plus code, QuantEcon-style). It
   duplicates QuantEcon, and it moves the project toward exam prep that
   CFA Institute's marks rules constrain (ROADMAP §5).

## Decision outcome

Chosen option: **1, the model layer**, because it is the gap the
neighbours leave open, and it keeps scope, licensing and regulation
manageable for one person.

**What pyeconomics is.**

- A registry of tested, cited models.
- Each model is a pure function with typed inputs and outputs. It never
  fetches data, prints, plots or calls an LLM.
- Each model is served identically to Python, the CLI, the REST API, MCP,
  the web app and, later, Excel.
- Every result carries a provenance manifest.
- Data reaches models through declared bindings that the data layer
  resolves (ROADMAP §3).

**Relations to neighbours.**

| Neighbour | Stance |
|-----------|--------|
| OpenBB | Integrate. OpenBB can be an optional meta-provider, and pyeconomics can be an OpenBB extension (Phase 6). Never a hard dependency, and never an AGPL OpenBB extension (ADR-0004). |
| QuantEcon | Complement. Link to and cite its lectures; never adapt their text. |
| FinanceToolkit | Differentiate, on breadth, verification and surfaces. |
| FinancePy, rateslib | Never depend on them. Their licences exclude them (ADR-0004). |
| QuantLib | A test oracle, and possibly an optional engine. |
| Fed rule tools (Atlanta Fed, Cleveland Fed) | Reproduce their outputs in tests (ROADMAP §4 2.4). |

**The maintainer's portfolio system.** pyeconomics may become a
dependency of it, never the reverse. No pyeconomics module imports it,
and no pyeconomics feature exists only to serve it.

**Out of scope** (ROADMAP §6), unless a superseding ADR changes it:

- portfolio-management, backtesting, order-management or trading systems;
- reselling or redistributing licensed data, or any proprietary data
  business;
- real-time streaming quotes, tick data and intraday terminal features;
- personalised investment advice or recommendations;
- exam-prep question banks, and any reproduction of curriculum material;
- full DSGE estimation suites (Dynare-class) and a symbolic algebra
  engine. Small linear New Keynesian and RBC simulators are in scope
  (Phase 7);
- native mobile and desktop apps beyond `pip`, `pipx` and `uv tool`;
- non-English localisation;
- self-hosted enterprise distributions and single sign-on, unless Phase 8
  evidence asks for them.

### Consequences

Good:

- A request outside the model layer has a written answer.
- The project integrates with the largest neighbour instead of racing it.
  OpenBB's move to Apache-2.0 [S1] makes that integration licence-clean
  for the core.
- Keeping models pure is what makes cross-surface parity testable.

Bad:

- Users who want an end-to-end workflow (data, models, portfolio) must
  combine pyeconomics with other tools.
- Model pages need data the project does not host. They rely on
  integrations and the user's own sources (ADR-0005).
- Some popular features (signals, backtests) are refused even when users
  ask for them.

### Confirmation

| Check | Built in |
|-------|----------|
| Unit tests run with sockets disabled (`pytest-socket`), so no model can touch the network | Phase 1 Step 9; Phase 2 acceptance |
| `registry.validate()` rejects a model without its card, references and typed inputs; a model's `compute` is pure | Phase 2 (ROADMAP §4 2.2) |
| The licence allowlist blocks FinancePy, rateslib and AGPL packages from the runtime set | Phase 1 Step 8 |
| The model-request issue form links this ADR and ROADMAP §6, and requires a citation | Phase 1 Step 11 (added to its task by this step) |
| Review: the maintainer closes out-of-scope issues and PRs by citing this ADR | Ongoing |

## More information

- Related: ADR-0004 (licences), ADR-0005 (data), ROADMAP §1 "Where
  pyeconomics fits", §5 "pyeconomics' own licence, name and posture".
- Sources, all accessed 2026-10-05:
  - [S1] OpenBB licence change: PR #7677 (merged 2026-09-24),
    https://github.com/OpenBB-finance/OpenBB/pull/7677; release
    `openbb-v5.0.0` (2026-09-30),
    https://github.com/OpenBB-finance/OpenBB/releases/tag/openbb-v5.0.0;
    PyPI `openbb` 5.0.0 licence Apache-2.0, https://pypi.org/pypi/openbb/json.
  - [S2] OpenBQ, https://openbq.org/; the repository now lives at
    https://github.com/openbq-org/OpenBB.
  - [S3] OpenBB blog, "OpenBB belongs to everyone" (2026-08-25),
    https://openbb.co/blog/openbb-belongs-to-everyone/.
  - [S4] QuantEcon.py (MIT), https://github.com/QuantEcon/QuantEcon.py.
  - [S5] QuantEcon lectures, licensed CC BY-SA 4.0 (site footer),
    https://python.quantecon.org/intro.html.
  - [S6] FinanceToolkit (MIT), https://github.com/JerBouma/FinanceToolkit.
  - [S7] FinancePy (GPL-3.0; PyPI 1.1.2 `GPL-3.0-or-later`),
    https://github.com/domokane/FinancePy.
  - [S8] rateslib LICENCE, https://github.com/attack68/rateslib/blob/main/LICENCE.
  - [S9] QuantLib licence (modified BSD), https://www.quantlib.org/license.shtml.
