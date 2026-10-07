# web/

Placeholder. Phase 5 builds the pyeconomics web app here: an Astro static
site with React islands, written in TypeScript and shared by the local app
(`pyeconomics serve`) and the hosted site. The stack and its hosting are
decided in [ADR-0006](../docs/adr/0006-web-stack-and-hosting.md).

Nothing in this directory ships in the `pyeconomics` wheel. Under ADR-0002,
the built site ships in its own `pyeconomics-app` wheel.
