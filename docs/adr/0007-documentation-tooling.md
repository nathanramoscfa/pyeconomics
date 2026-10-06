# ADR-0007: Documentation tooling

- Status: Accepted
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6, 2.5 and 5.6

## Context and problem

pyeconomics' documentation has to do four things:

- carry a generated reference for hundreds of models (ROADMAP §4 2.5);
- run tutorials and how-to guides as executable notebooks;
- hold a gallery of worked examples;
- prove that every code sample still runs (ROADMAP §4 5.6).

The 0.2.x site is Sphinx on Read the Docs. Since Phase 1 Step 4, the Read
the Docs project's `stable` and `latest` serve 0.2.x from `legacy/0.2.x`
(`docs/releases/0.2.6-readiness.md`, Release record V6). It keeps doing so
until Phase 5.

The Python documentation landscape changed in the last year:

- Material for MkDocs, the most popular MkDocs theme, entered maintenance
  mode on 2025-11-05, with a commitment to fix critical bugs and security
  issues for at least 12 months [S6]. That commitment runs to about
  November 2026.
- Its authors' successor, Zensical, is at 0.0.68 and classed Alpha [S7].
- MkDocs itself has had no release since 1.6.1 in August 2024. MkDocs 2.0
  is announced as a rewrite that removes the plugin system [S8].

## Decision drivers

- An API reference generated from the source, without importing the
  package at build time.
- Notebooks executed during the build, so a broken example fails CI.
- Doctests for Markdown pages, not only for docstrings.
- Maintained tools with a long record, because the docs outlive any one
  phase.
- Free hosting for an open-source project, with versioned docs (`latest`,
  `stable`, per release).

## Considered options

1. **Sphinx with MyST-NB, sphinx-autoapi and sphinx-gallery on Read the
   Docs; Sybil for Markdown doctests.**
   - Sphinx 9.1.0 [S1] is the long-standing standard for Python API docs.
   - MyST-NB 1.4.0 [S2] parses MyST Markdown and executes notebooks.
   - sphinx-autoapi 3.8.1 [S3] builds the reference by parsing source
     rather than importing it, and is now maintained under the Read the
     Docs GitHub organization [S3].
   - sphinx-gallery 0.22.1 [S4] turns example scripts into a gallery.
   - Sybil 10.1.0 has Markdown and MyST parsers that run under pytest [S5].
2. **Material for MkDocs with mkdocstrings.** Good-looking and fast to
   author, but the theme is in maintenance mode with an end date about a
   month away [S6], and the MkDocs core is unmaintained and heading for an
   incompatible 2.0 [S8]. Choosing it now would mean a forced migration
   during Phase 5.
3. **Zensical.** The likely successor to Material for MkDocs, and it aims
   to build existing MkDocs projects with few changes [S7]. It is alpha
   (0.0.68), so it is not a foundation for a 1.0 launch today.

## Decision outcome

Chosen option: **1**, because each part is mature and maintained, it keeps
the Read the Docs project and URLs 0.2.x users already know, and it is the
only option that generates a reference, executes notebooks and runs
Markdown doctests today.

**The stack.**

- Sphinx, with MyST Markdown as the authoring format through MyST-NB.
- sphinx-autoapi for the generated API reference.
- sphinx-gallery for example galleries.
- Read the Docs Community hosting, which is free for open-source projects
  and ad-supported [S9].
- Model pages are generated from each model's spec (ROADMAP §4 2.5) and
  are not written by hand.

**Executable examples.**

- Docstring examples run as doctests.
- Markdown pages run through Sybil under pytest.
- Notebooks execute during the docs build, and a failure fails the build.
- In-browser examples use marimo's WebAssembly HTML export [S10], as
  ROADMAP §4 5.6 plans.

**Hosting until Phase 5.**

- Read the Docs keeps serving 0.2.x as `stable` and `latest`.
- Phase 2 publishes the 1.0 docs skeleton as a preview, never as the
  default version. Phase 2's roadmap chooses the mechanism.
- Phase 5's cutover points `stable` at 1.0.0 (ROADMAP §4 5.10).

**Revisit at Zensical 1.0.** When Zensical reaches 1.0, a new ADR
evaluates it against this stack: reference generation, notebook execution,
versioned hosting, and the cost of migrating. Until then, nothing in the
docs depends on MkDocs.

### Consequences

Good:

- One mature toolchain covers reference, narrative, notebooks and gallery,
  with examples that cannot silently rot.
- Read the Docs keeps the existing project, its URLs and versioned builds
  at no cost.
- sphinx-autoapi's static parsing means the docs build needs no optional
  extras installed.

Bad:

- Sphinx configuration and themes are heavier to learn than MkDocs.
- Read the Docs Community shows ads on the docs. Removing them is a paid
  plan (TBD; not needed now).
- Executing notebooks in CI lengthens the docs build, and notebooks that
  need live data need cached inputs or skips.
- The revisit trigger depends on another project's timeline.

### Confirmation

| Check | Built in |
|-------|----------|
| Doctests on every public docstring (`pytest --doctest-modules`) | Phase 1 Step 9 |
| Docs build in CI with warnings as errors, notebooks executed; Sybil collects Markdown examples under pytest | Phase 2 (ROADMAP §4 2.5) |
| Generated model pages: every registered model has a docs page (`registry.validate()` plus a docs-page count check) | Phase 2 (ROADMAP §4 2.5) |
| Read the Docs `stable` serves 1.0.0 and its version banner matches | Phase 5 (ROADMAP §4 5.10) |

## More information

- Related: ADR-0006 (the web app's model pages are separate from the docs),
  ADR-0003 (docs versions follow release tags), ROADMAP §5 "Deployable
  surfaces" (Documentation row).
- Sources:
  - [S1] PyPI, `sphinx` 9.1.0 (2025-12-31), BSD-2-Clause,
    https://pypi.org/pypi/sphinx/json, accessed 2026-10-05.
  - [S2] PyPI, `myst-nb` 1.4.0 (2026-03-02),
    https://pypi.org/pypi/myst-nb/json; repository active (commits July and
    August 2026), https://github.com/executablebooks/MyST-NB, both accessed
    2026-10-05.
  - [S3] PyPI, `sphinx-autoapi` 3.8.1 (2026-08-23), MIT, maintained under
    the `readthedocs` GitHub organization,
    https://pypi.org/pypi/sphinx-autoapi/json, accessed 2026-10-05.
  - [S4] PyPI, `sphinx-gallery` 0.22.1 (2026-09-18), BSD-3-Clause,
    https://pypi.org/pypi/sphinx-gallery/json, accessed 2026-10-05.
  - [S5] Sybil 10.1.0 (2026-06-13), MIT, `sybil.parsers.markdown` and
    `sybil.parsers.myst`, https://sybil.readthedocs.io/en/latest/, accessed
    2026-10-05.
  - [S6] Material for MkDocs blog, 2025-11-05: "We commit to supporting
    Material for MkDocs for at least the next 12 months, fixing critical
    bugs and security vulnerabilities as needed",
    https://squidfunk.github.io/mkdocs-material/blog/2025/11/05/zensical/,
    accessed 2026-10-05.
  - [S7] PyPI, `zensical` 0.0.68 (2026-10-05), "Development Status :: 3 -
    Alpha", https://pypi.org/project/zensical/; Zensical roadmap,
    https://zensical.org/roadmap/, both accessed 2026-10-05.
  - [S8] Material for MkDocs blog, 2026-02-18, on MkDocs 2.0 (a rewrite that
    removes the plugin system; MkDocs 1.6.1 of 2024-08-30 is the last 1.x
    release), https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/,
    accessed 2026-10-05.
  - [S9] Read the Docs pricing: Community, "Free for open-source software",
    ad-supported hosting, https://about.readthedocs.com/pricing/, accessed
    2026-10-05.
  - [S10] marimo WebAssembly HTML export (`marimo export html-wasm`),
    https://docs.marimo.io/guides/exporting/webassembly_html/, accessed
    2026-10-05.
