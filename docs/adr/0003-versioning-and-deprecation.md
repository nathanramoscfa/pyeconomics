# ADR-0003: Versioning and deprecation

- Status: Accepted
- Date: 2026-10-05
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: ROADMAP §4 1.6; §5 "Release & tagging" and "Versioning"

## Context and problem

pyeconomics has shipped 0.1.0 and 0.2.0 to 0.2.6 on PyPI. The 1.0 rebuild
replaces the 0.2.x package outright, reaches users through eight phases of
pre-releases, and from Phase 4 serves the same models through a CLI, a REST
API and an MCP server whose callers cannot read a changelog before every
call. Users need to know three things: when the API stops changing under
them, how much warning they get before something goes, and what happens to
0.2.x.

Two facts constrain the answer:

- In 0.2.x, a tag and its package version could disagree, because the
  release workflow wrote a version file that `setup.py` never read
  (ROADMAP §2, gap 5).
- pip installs pre-releases only with `--pre` or when a specifier names one
  [S3]. So `1.0.0` pre-releases on PyPI leave a plain
  `pip install pyeconomics` on 0.2.6 until 1.0.0 itself ships.

## Decision drivers

- Users who pin pyeconomics, and agents that call it, can tell a breaking
  change from a safe one by the version number alone.
- One person can follow the policy without judgement calls at release time.
- 0.2.x users are never moved to 1.0 by surprise, and the end of their
  support matches what the 0.2.6 advisory already promised.
- A tag can never again disagree with the version it publishes.

## Considered options

1. **PEP 440 versions with Semantic Versioning meaning, 1.0.0 at launch.**
   0.x was initial development; 1.0.0 is the first stable API; pre-releases
   mark each phase.
2. **Calendar versioning (for example `2026.10`).** Says when, not what. It
   suits data snapshots, not a library whose users need to know whether an
   upgrade breaks their code.
3. **Keep 0.x until the catalog is complete.** Under SemVer, 0.x promises
   nothing [S2], so users would wait through Phase 7 for any stability
   guarantee. Rejected: Phase 5's public launch needs a stable API to point
   people at.

## Decision outcome

Chosen option: **1, PEP 440 versions with Semantic Versioning meaning**,
because it is the convention Python users already read, and it gives a
precise answer to "will this upgrade break me?".

**Version numbers.**

- Every version is a valid PEP 440 version [S1] and follows Semantic
  Versioning 2.0.0 [S2] (MAJOR.MINOR.PATCH).
- 0.x was initial development. **1.0.0, released at the Phase 5 launch, is
  the first stable public API.** After it, any breaking change needs 2.0.0.
- The 1.0.0 pre-releases carry no stability promise. A pre-release may
  break the one before it, and its release notes say how.

**One pre-release per phase.** These are the milestones in ROADMAP §5
"Release & tagging":

| Tag | Phase | Index |
|-----|-------|-------|
| `v1.0.0.dev1` | 1: skeleton and publishing pipeline | TestPyPI only |
| `v1.0.0a1` | 2: model engine and core catalog | PyPI pre-release |
| `v1.0.0a2` | 3: data platform and monetary-policy suite | PyPI pre-release |
| `v1.0.0b1` | 4: CLI, REST API, MCP server and exports | PyPI pre-release |
| `v1.0.0rc1` | 5: release candidate through the launch gate | PyPI pre-release |
| `v1.0.0` | 5: public launch | PyPI, stable |

After 1.0.0, Phases 6 and 7 release minor versions in merge order, and
fixes ship as patch releases.

**What is public API after 1.0.0.** Breaking any of these needs a major
version:

- Python names importable from `pyeconomics` without a leading underscore
  and documented in the reference.
- Model ids, input and output field names, units and their JSON Schemas.
- CLI commands and options, REST paths and schemas, and MCP tool names and
  schemas.
- The canonical JSON result format and the manifest schema.

These are not breaking changes:

- Adding a model, an optional input, an output field or an extra.
- Correcting a wrong number. It is an errata fix: the model's own version
  goes up, the manifest records it, and the errata page logs it (ROADMAP §5
  "Model quality & governance").
- Raising the Python floor as ADR-0010 schedules it, announced in the
  changelog.

**Model ids are permanent.** Once released, a model id is never deleted or
given to a different model. A renamed model keeps its old id as an alias
that warns. Model versions are separate from the package version: a model's
version goes up whenever its outputs change, and every manifest records
both versions.

**Deprecation.** A public name or behaviour is removed only in a major
release. Before that, at least one minor release must have warned about
it. The warning:

- is visible by default (a `FutureWarning` subclass; Phase 2 defines it);
- names the replacement and the release that removes the old name;
- is listed under "Deprecated" in the changelog.

The roadmap's "one minor release of warnings" therefore sets the minimum
warning period, and SemVer sets the release the removal ships in.

**Tags.**

- A release tag is `v` followed by the version in `pyproject.toml`, and the
  release workflow refuses any tag that does not match it.
- Release tags are cut from `main` only. `v0.*` tags belong to
  `legacy/0.2.x` and its own workflow.

**0.2.x.**

- `legacy/0.2.x` takes security fixes only, as 0.2.7 and later.
- 0.2.x reaches end of life when 1.0.0 is released. These are the words the
  0.2.6 CHANGELOG, README notice and advisory GHSA-j6rp-vwwv-jrr8 already
  use [S4][S5].
- Its releases stay on PyPI. Pins such as `pyeconomics<1` keep working.

### Consequences

Good:

- Users and agents can upgrade within 1.x without reading the changelog
  first, and `<2` is a safe pin.
- `pip install pyeconomics` keeps resolving 0.2.6 until 1.0.0 ships, so
  nobody is moved to a pre-release by accident.
- Tag and version can no longer disagree.
- Permanent ids keep every saved result, manifest, notebook and MCP
  transcript resolvable.

Bad:

- After 1.0.0, a design mistake in a public name lives until 2.0.0 behind a
  deprecation shim. This raises the stakes on Phase 2's contracts and on
  Phase 4's generated surfaces.
- The model registry carries aliases and deprecated names indefinitely.
- 0.2.x users get no fixes after 1.0.0 except by upgrading to a rewritten
  API. The Phase 5 migration guide (ROADMAP §4 5.6) is their path.

### Confirmation

| Check | Built in |
|-------|----------|
| `release.yml`'s `verify` job: the tag equals `v` plus `uv version --short`, the tagged commit is on `main`, `v0.*` is refused, and `.devN` goes to TestPyPI only | Phase 1 Step 10 |
| One version source: a static version in `pyproject.toml`, read through `importlib.metadata`; `tests/unit/test_version.py` asserts that `pyeconomics.__version__` equals it | Phase 1 Step 7 |
| `pr-title`: Conventional Commits titles, so `!` and `BREAKING CHANGE` mark breaking changes in review and in the squash message | Phase 1 Step 10 |
| `CHANGELOG.md` in Keep a Changelog form, with Deprecated and Removed sections | Phase 1 Step 11 |
| `registry.validate()`: rejects a released model id that has gone missing or been reused; aliases resolve | Phase 2 (ROADMAP §4 2.2) |
| Each phase's release step checks its milestone tag against the table above | Phases 2–5 release steps |

## More information

- Related: ADR-0002 (what ships in each distribution), ADR-0010 (Python
  floor changes are minor-release events), ROADMAP §5 "Release & tagging"
  and "Versioning".
- Sources:
  - [S1] PEP 440, Version Identification and Dependency Specification,
    https://peps.python.org/pep-0440/, accessed 2026-10-05.
  - [S2] Semantic Versioning 2.0.0 (item 4: major version zero is for
    initial development; item 5: 1.0.0 defines the public API),
    https://semver.org/spec/v2.0.0.html, accessed 2026-10-05.
  - [S3] pip 26.2.1 documentation, `pip install`, "Pre-release Versions":
    pip installs only stable versions by default, unless `--pre` is given
    or a specifier names a pre-release,
    https://pip.pypa.io/en/stable/cli/pip_install/, accessed 2026-10-05.
  - [S4] GHSA-j6rp-vwwv-jrr8,
    https://github.com/nathanramoscfa/pyeconomics/security/advisories/GHSA-j6rp-vwwv-jrr8,
    accessed 2026-10-05.
  - [S5] `docs/releases/0.2.6-readiness.md` §8.3: "0.2.x receives security
    fixes only and reaches end-of-life when pyeconomics 1.0.0 is released".
