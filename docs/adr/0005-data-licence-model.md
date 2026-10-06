# ADR-0005: Data-licence model

- Status: Proposed
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6; §5 "Data licensing policy" and "Data terms"

## Context and problem

pyeconomics feeds models with data from many sources, and their terms
differ sharply. The same series can be free to display on a public website
from one source and forbidden to cache from another. Two examples:

- **FRED.** The terms bar storing, caching or archiving FRED content and
  giving a stored copy to third parties. They bar using it to develop or
  train machine-learning or generative-AI models. They allow commercial use
  only internally or in reports to clients, for series labelled public
  domain or copyrighted with citation. They forbid "FRED®", "ALFRED®" or
  "Federal Reserve Bank" in an application's hostname, and replicating
  FRED's essential user experience [S1].
- **Coin Metrics.** Its community data is licensed CC BY-NC 4.0, so no
  commercial use [S2].

0.2.x ignored this. It cached FRED responses in a pickle file (ROADMAP §2,
gap 4).

1.0 serves data through two very different channels:

- **The user's machine.** The library, CLI, local app and MCP server run
  under the user's own credentials and their own acceptance of each
  source's terms.
- **The hosted service.** A public website and API, from Phase 5, that
  pyeconomics itself operates.

A source that is fine in the first channel can be a terms violation in the
second. The project needs one model, enforced in code, that decides where
each source's data may flow.

## Decision drivers

- No hosted surface ever serves data its source's terms forbid it to serve.
- Users keep full local access to every source they are entitled to.
- The rule is enforced by code and tests, not by reviewer memory.
- Attribution and required notices travel with the data automatically.
- A change in a provider's terms is caught and acted on, not discovered
  later.

## Considered options

1. **Five licence classes as provider metadata, with hosted mode refusing
   everything except `hosted-safe` and `user-supplied`.** This is the model
   ROADMAP §5 "Data licensing policy" sets out.
2. **Per-source judgement at review time, with no class in code.** Cheap to
   start, but nothing stops a later change from routing a library-only
   source into the hosted service.
3. **Free public sources only, everywhere.** Safe, but it drops FRED,
   ALFRED, Ken French, yfinance, Bloomberg and bring-your-own-key
   providers. Those are much of what local users need (Phases 3 and 6).

## Decision outcome

Chosen option: **1**, because it keeps every local capability and makes
the hosted boundary a property the code enforces and the tests prove.

**Classes.** Every provider declares exactly one class, and so does every
series when one source mixes classes:

| Class | Meaning | Library, CLI, local app, MCP | Hosted service |
|-------|---------|------------------------------|----------------|
| `hosted-safe` | Terms allow display by a third-party service, with attribution | Yes | Yes: snapshot, display and export, with attribution |
| `library-only` | Personal-use, non-commercial, no-caching or scraped terms | Yes, under the user's own acceptance of the terms | Never, unless the owner grants written permission |
| `byok` | The user's own paid subscription | Yes, on the user's key | Never, except from Phase 8 a per-request pass-through the vendor allows |
| `premium-local` | Licensed to a machine or seat | Yes, on the licensed machine only | Never |
| `user-supplied` | The user's own files | Yes | Processed in memory for one run, never stored |

**Rules.**

1. **Enforced in code.**
   - The class is required metadata on every provider, together with its
     terms URL and the date the terms were last checked.
   - Where one source mixes classes, the series carries the class. The
     source's own markers decide it: FRED's copyright labels [S1], the
     World Bank's `License_Type` field [S3], and Eurostat's listed
     exceptions [S4].
   - Hosted mode refuses any source not classed `hosted-safe` or
     `user-supplied`.
2. **Attribution travels with the data.** Every chart, table, export and
   manifest carries the source's attribution and terms link, including
   each required notice:
   - FRED: "This product uses the FRED® API but is not endorsed or
     certified by the Federal Reserve Bank of St. Louis." [S1]
   - BEA: "This product uses the Bureau of Economic Analysis (BEA) Data
     API but is not endorsed or certified by BEA." [S5]
   - Census: "This product uses the Census Bureau Data API but is not
     endorsed or certified by the Census Bureau." [S6]
3. **Originators, not aggregators.**
   - The hosted service snapshots public series from the agency that
     publishes them, never through FRED or another aggregator.
   - It reads those snapshots rather than calling providers per request.
   - It never relays a user's own key, because that is redistribution too.
4. **Caching follows the terms.** A source whose terms forbid storage is
   fetched live and never written to disk. FRED is one [S1].
5. **Feed models, don't clone providers.** The hosted data explorer exists
   to feed models. It never replicates a provider's own product, as FRED's
   terms require [S1].
6. **Charge for compute and features, never for raw data.**
   - BIS statistics in a commercial product may not add any charge to
     users [S7].
   - In anything sold, ECB-sourced information needs a notice, shown
     before payment and on each access, that it "may be obtained free of
     charge" from the ECB [S8].
   - IMF data sold on its own needs a notice that it is free from the IMF
     [S9].
7. **A terms change is a High defect.** Reclassify the source, purge any
   hosted snapshot it no longer allows, and record the change in the
   changelog.

**Classifying a source.**

- A source is classified from its own terms page before its provider
  merges, and re-checked yearly and whenever the source changes.
- ROADMAP §5 "Data licensing policy" lists each source's expected class.
  That list is a plan, and the provider's merge confirms each entry.
- Anchor facts verified for this ADR:
  - FRED and ALFRED, Ken French [S10], yfinance (Yahoo data "intended for
    personal use only" [S11]), Coin Metrics [S2] and the IMF (commercial
    reuse and automated bulk download need the IMF's explicit permission
    [S9]) are `library-only`.
  - The World Bank's CC BY 4.0 default with per-dataset exceptions [S3]
    and Eurostat's commercial reuse with attribution, minus its listed
    exceptions [S4], are `hosted-safe` at series level.
  - Tiingo licenses software in which users submit their own token, while
    serving its data to others needs a redistribution licence [S12]. That
    makes it `byok`, with a pass-through possible from Phase 8.
  - OECD's own terms page could not be read at the access date. Its July
    2024 move to CC BY 4.0 is confirmed for publications and content, but
    not formally for data. OECD's class is therefore TBD until its provider
    merges in Phase 3.
- This is engineering policy, not legal advice. Counsel reviews it before
  the Phase 5 launch (ROADMAP §5 "Legal & brand guardrails").

### Consequences

Good:

- The hosted service cannot serve a library-only source by mistake: the
  code refuses it, and a test proves it.
- Local users keep every source they are entitled to.
- Attribution is automatic, so no surface forgets a required notice.
- Fixtures and snapshots stay small and lawful. Golden tests keep only the
  few published values they need, each cited (ROADMAP §5 "Data terms").

Bad:

- The hosted site cannot run models whose only live data is library-only
  (Ken French, Shiller, AQR). Those pages run on the user's own data or
  point to the local app (ROADMAP §4 5.4).
- Series-level classes add metadata to maintain, and a yearly terms review
  to run.
- Snapshotting originators instead of calling FRED means more providers to
  build and keep working.
- Some calls, such as FRED content reaching an LLM at inference time,
  remain counsel questions. Until answered, hosted AI features use
  `hosted-safe` data only (ROADMAP §5 "Data terms").

### Confirmation

| Check | Built in |
|-------|----------|
| Provider contract: `licence_class`, terms URL and terms-checked date are required, and the registry rejects a provider without them | Phase 3 (ROADMAP §4 3.1) |
| Cache policy: a provider whose class or terms forbid storage has no cache path, and a test proves nothing is written | Phase 3 (ROADMAP §4 3.3) |
| Hosted-mode refusal: a test per class proves hosted mode rejects `library-only`, `byok` and `premium-local` sources; the hosted image omits their client libraries | Phases 4–5 (ROADMAP §4 4.4, 4.7, 5.8) |
| Attribution: every export and manifest carries the source's notice; a test per provider checks the exact wording | Phases 3–5 (ROADMAP §4 3.1, 5.7) |
| Fixtures hold no third-party dataset: the Step 5 security gate, and the provider review in every later phase | Phase 1 Step 5 onward |
| Yearly terms review and the reclassification runbook | Phase 5 (ROADMAP §5 "Runbooks") |

## More information

- Related: ADR-0002 (`[bloomberg]` and the provider extras), ADR-0006
  (hosted mode), ROADMAP §5 "Data licensing policy", "Data terms" and
  "Required notices".
- Sources, all accessed 2026-10-05:
  - [S1] FRED terms of use, https://fred.stlouisfed.org/legal/terms/; API
    clauses and the required notice,
    https://fred.stlouisfed.org/docs/api/terms_of_use.html; the June 2024
    terms update (ML and AI training),
    https://fred.stlouisfed.org/news/2024/06/weve-updated-our-terms-of-use-action-requested.
  - [S2] Coin Metrics Community Data (CC BY-NC 4.0),
    https://docs.coinmetrics.io/packages/coin-metrics-community-data.
  - [S3] World Bank dataset terms (CC BY 4.0 unless labelled otherwise),
    https://www.worldbank.org/ext/en/legal/terms-conditions/datasets; API
    metadata field `License_Type`, for example
    https://api.worldbank.org/v2/sources/2/series/NY.GDP.MKTP.CD/metadata?format=json.
  - [S4] Eurostat copyright notice,
    https://ec.europa.eu/eurostat/help/copyright-notice.
  - [S5] BEA API terms of service,
    https://apps.bea.gov/api/_pdf/bea_api_tos.pdf.
  - [S6] Census Bureau API terms of service,
    https://www.census.gov/data/developers/about/terms-of-service.html.
  - [S7] BIS data portal legal terms, https://data.bis.org/help/legal.
  - [S8] ECB website legal notice (copyright),
    https://www.ecb.europa.eu/services/disclaimer/html/index.en.html.
  - [S9] IMF copyright and usage,
    https://www.imf.org/en/About/copyright-and-terms.
  - [S10] Kenneth R. French Data Library ("Copyright Eugene F. Fama and
    Kenneth R. French"),
    https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html.
  - [S11] yfinance README, https://github.com/ranaroussi/yfinance.
  - [S12] Tiingo terms of service, https://app.tiingo.com/tos/; API
    overview, https://www.tiingo.com/documentation/general/overview.
  - OECD: terms page https://www.oecd.org/en/about/terms-conditions.html
    returned HTTP 403 to automated access. OECD's 2024-07-04 open-access
    announcement,
    https://www.oecd.org/en/about/news/press-releases/2024/07/oecd-data-publications-and-analysis-become-freely-accessible.html,
    was read through a mirror.
