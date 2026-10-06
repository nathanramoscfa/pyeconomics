# ADR-0006: Web stack and hosting

- Status: Proposed
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6; §3 Target Architecture; §5 "Cost projection" and
  "Release & deployment strategy"

## Context and problem

Phase 5 ships a web app in two modes from one build:

- **Hosted:** a public site with one prerendered page per model, a
  calculator on each, a data explorer, and an API.
- **Local:** `pyeconomics serve` serves the same pages and API on
  127.0.0.1, with every data source the user can access.

The pages are mostly static content: formula, explanation, variables,
citations. Interactivity is confined to calculators and charts. The site
must rank in search, load fast, pass WCAG 2.2 AA, and cost about nothing at
hobby scale (ROADMAP §5 "Cost projection"). One person runs it.

The API is the pyeconomics wheel itself, started in hosted mode. It must
scale to zero when idle, and its rollback must take minutes (ROADMAP §5
"Rollback").

## Decision drivers

- Page performance and indexability for a site of hundreds of model pages.
- The same built site serves both hosted and local modes, with no server
  needed for pages.
- Near-zero fixed cost, scale to zero, and per-request pricing that is easy
  to cap.
- Familiar tools: the maintainer already builds with React, Tailwind and
  shadcn/ui, and already runs services on Cloud Run.
- Python end to end on the server, so the API is the library.

## Considered options

1. **Astro static output with React islands; static site on Cloudflare;
   FastAPI on Cloud Run.** Astro prerenders every page to HTML by default
   [S1]. It hydrates only the calculator and chart components, through
   `@astrojs/react` [S2].
2. **Next.js.** A strong framework for a logged-in application, MIT and
   current at 16.3.8 [S6]. For a content site of prerendered pages, it
   ships more client JavaScript and assumes a Node server or a vendor
   platform to get the most from it. That is weight the Phase 5 site does
   not need.
3. **Fly.io for the API instead of Cloud Run.** Comparable runtime, but
   new organizations are pay-as-you-go with only a short trial [S9]. Cloud
   Run has a monthly free tier and scales to zero by default [S7][S8], and
   the maintainer already operates it.
4. **A Python-rendered site (FastAPI templates, or a Python web framework).**
   Puts a server behind every page view, which conflicts with static
   hosting, zero-cost idling and the local app's offline serving.

## Decision outcome

Chosen option: **1**, because it serves static pages from a CDN at no cost,
hydrates only what is interactive, reuses the maintainer's React toolkit,
and runs the API as the library itself.

**Frontend (`web/`).**

- Astro with static output and React islands, in TypeScript.
- Tailwind CSS and shadcn/ui. shadcn/ui documents an Astro install path
  [S3][S4].
- Versions are pinned in `web/`'s lockfile when Phase 5 creates it. At
  the access date, Astro's major is 7, React's 19 and Tailwind's 4.
- KaTeX for formulas, Plotly.js for charts (the same figure JSON the
  library emits), RJSF for schema-driven forms, and the generated
  TypeScript client, as ROADMAP §4 5.1 lists.

**Static hosting.**

- Cloudflare serves the built site, with DNS, TLS, CDN, WAF and rate rules
  in front of everything.
- Cloudflare now tells new projects to start on Workers rather than Pages
  [S5], and static-asset requests on Workers are free and unlimited [S5].
  Phase 5 therefore deploys the site as Workers static assets unless its
  roadmap finds a reason to stay on Pages.
- Either way, the site stays static: no Worker code sits in the page path
  unless a later ADR adds it.

**API hosting.**

- FastAPI on Google Cloud Run, the same wheel started in hosted mode.
- Minimum instances are 0 and the maximum instance count is capped.
- Previous revisions are kept for minute-scale rollback.

**Next.js only by a superseding ADR,** if a logged-in application ever
becomes the main experience (Phase 8 at the earliest).

### Consequences

Good:

- Pages are plain HTML from a CDN. They are fast, indexable and cheap, and
  `pyeconomics serve` can serve the same files from the `[app]` wheel
  (ADR-0002).
- Only calculators and charts ship JavaScript.
- Cloudflare's static requests and Cloud Run's free tier keep the hosted
  site at about $0 a month at hobby scale [S5][S7], matching ROADMAP §5
  "Cost projection".
- Cloud Run revisions give the minute-scale rollback ROADMAP §5 promises.

Bad:

- Two languages (TypeScript and Python) and two toolchains in one
  repository.
- Cloud Run cold starts add latency to the first request after idling.
- Cloudflare is a single vendor for DNS, CDN, WAF and static hosting, and
  its products move: Pages to Workers is one such shift. A move is cheap
  because the site is static files.
- Astro's major version has moved often. 7.0.0 shipped in June 2026 [S1],
  so Phase 5 must expect a major upgrade during the 1.x line.

### Confirmation

| Check | Built in |
|-------|----------|
| `web/` scaffold: Astro static output, `@astrojs/react`, Tailwind, shadcn/ui; Vitest and Playwright; a build check that fails if a page route needs server rendering | Phase 5 (ROADMAP §4 5.1) |
| Deploy workflow: static site to Cloudflare, API to Cloud Run behind the protected `production` environment; `/version.json` and `/version` report the release SHA | Phase 5 (ROADMAP §4 5.8; §5 "Deployable surfaces") |
| Cloud Run settings by API read: minimum instances 0, maximum capped; budget alert fires once | Phase 5 (ROADMAP §4 5.8–5.9) |
| Phase 4's staging service already runs on Cloud Run's free tier | Phase 4 (ROADMAP §4 4.7) |

## More information

- Related: ADR-0002 (`pyeconomics-app` wheel behind `[app]`), ADR-0005
  (hosted mode serves `hosted-safe` and `user-supplied` data only),
  ADR-0007 (the documentation site is separate, on Read the Docs).
- Sources:
  - [S1] npm registry, `astro` latest 7.3.5 (2026-09-24), MIT, 7.0.0
    released 2026-06-22, https://registry.npmjs.org/astro/latest; Astro
    docs: "By default, your entire Astro site will be prerendered",
    https://docs.astro.build/en/guides/on-demand-rendering/, both accessed
    2026-10-05.
  - [S2] `@astrojs/react` 7.0.0, MIT, client-side hydration of React 17–19
    components, https://docs.astro.build/en/guides/integrations-guide/react/,
    accessed 2026-10-05.
  - [S3] shadcn/ui Astro installation (`shadcn@latest init -t astro`),
    https://ui.shadcn.com/docs/installation/astro, accessed 2026-10-05.
  - [S4] npm registry: `tailwindcss` 4.3.3 (MIT), `react` 19.3.0 (MIT,
    2026-09-09), https://registry.npmjs.org/, accessed 2026-10-05.
  - [S5] Cloudflare Pages docs ("Start new projects with Workers"),
    https://developers.cloudflare.com/pages/; Workers static assets, "Requests
    to static assets are free and unlimited",
    https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/,
    both accessed 2026-10-05.
  - [S6] npm registry, `next` 16.3.8 (2026-09-30), MIT,
    https://registry.npmjs.org/next/latest, accessed 2026-10-05.
  - [S7] Cloud Run pricing, free tier per billing account: request-based
    billing 2 million requests, 180,000 vCPU-seconds and 360,000
    GiB-seconds a month, https://cloud.google.com/run/pricing, accessed
    2026-10-05.
  - [S8] Cloud Run instance autoscaling: a revision with no traffic scales
    to zero by default,
    https://docs.cloud.google.com/run/docs/about-instance-autoscaling,
    accessed 2026-10-05.
  - [S9] Fly.io pricing: "New organizations use Pay As You Go pricing",
    with a trial only, https://docs.fly.io/about/pricing, accessed
    2026-10-05.
