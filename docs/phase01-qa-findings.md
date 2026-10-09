<!-- docs/phase01-qa-findings.md -->

# Phase 1 QA findings

Phase 1 (Reset & Foundation) closes with this record: every finding Steps 1–12
surfaced, its Triage class (ROADMAP §5 "Defect handling & triage"), where it went,
and the guard that now prevents the class. The executable record is
`scripts/verify-phase01.sh`. Its static checks run on every pull request and every
push to `main` (`.github/workflows/phase-verify.yml`). Its `--live` and `--post`
checks run on the maintainer's machine.

Destinations are a pull request (fixed), an issue number, a roadmap edit, or the
phase that owns the item. Nothing here is left without one.

## Step 1 — Preserve 0.2.x and land the roadmaps (PR #46)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| GitHub requires unique ruleset names (`422 Name must be unique`), so the archive ruleset became two: `archive-immutable-branches` and `archive-immutable-tags` | spec-rot | Roadmap edited in PR #46 (Step 1, Step 12, V1.4) | V1.4 checks both names (`--live`) |
| The 0.2.x pytest suite was red on its own pins (ROADMAP §2 gap 2) | bug | Owned by 0.2.x's retirement: Step 2 made the legacy CI green, and Step 7 removed 0.2.x from `main` | V2.2 checks legacy CI green on 3.11 and 3.12 |

## Step 2 — Legacy credential-logging fix and hardened pipeline (PRs #47, #48)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| 0.2.x logged the FRED API key at DEBUG level | security | Fixed in PR #47 and shipped in 0.2.6 (GHSA-j6rp-vwwv-jrr8) | `tests/test_credential_logging.py` and the release smoke on `legacy/0.2.x`; static check 6; the semgrep `credential-logging` rule on `main` |
| The first TestPyPI publish failed with `invalid-publisher`: no pending publisher was registered | process | Fixed by the operator; run attempt 2 passed | Step 3's access-control section re-checks every publisher |
| Earlier operator confirmations did not match what was configured | process | Re-done; Step 3 re-confirmed each one on the provider pages | Step 3 access-control evidence |
| Auto mode denies protection, secret, merge and publish actions one at a time | process | Agent memory; CLAUDE.md asks for them once, at the start of the step | CLAUDE.md "Claude Code specifics" |
| Step 3's artifact diff must expect four differences and compare `Requires-Dist` as parsed requirements | spec-rot | Roadmap edited in PR #48 | Step 3 criterion |
| 27 pip-audit advisories in 0.2.x's pinned jupyterlab, pytest and setuptools | security | Assessed in Step 3; shipped as "Known issues" in 0.2.6 (PR #50). 0.2.x is security-only and ends at 1.0.0 (ADR-0003) | `pip-audit` hook on `main` |
| 0.2.x defects out of scope: a half-built singleton, `tests/` shipped in the wheel, a pickle cache | bug | Not fixed by decision (ADR-0003: 0.2.x is security-only); 1.0 replaces them | semgrep `unsafe-deserialization` rule; `dist_contents.py` allowlist |

## Step 3 — 0.2.6 readiness gate (PR #49)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| The CHANGELOG and README said "0.2.5 and earlier", but the affected range is 0.2.0–0.2.5 (readiness §4.3, §8.4) | spec-rot | Step 4's task edited in PR #49, fixed in PR #50; ROADMAP 1.1 corrected | V4.3 checks the advisory's range |
| A user-level uv index (a private package firewall) took over TestPyPI installs | process | Steps 4 and 5 use `--no-config`; AGENTS.md rule | `lock-index` hook (Step 8) |
| TestPyPI's JSON API lags behind a yank | process | The rollback procedure reads the Simple API (readiness §7) | Readiness §7 |

## Step 4 — 0.2.6 security release and advisory (PRs #50, #51)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| The advisory published before GitHub assigned its CVE id | security | Issue #52 (open; the maintainer records the id when GitHub assigns it). The criterion was amended with the maintainer's approval | V4.3 checks the published advisory |

## Step 5 — Characterize and archive 0.2.x (PR #53)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| 15 Dependabot alerts were open on `main`, but Step 8's context said alerts were off | spec-rot | Roadmap edited in PR #53; the alerts closed when Step 7 removed 0.2.x | V8.4 checks Dependabot alerts and security updates |
| A Code Climate webhook was left over from 0.2.x | security | Step 8's context gained a webhook audit; Step 8 deleted it | Step 8 webhook audit |
| The DCF prototype under `dev/` is a 0-byte file | process | Recorded in the private archive's `INDEX.md` | V5.3 |

## Step 6 — Architecture decision records (PR #54)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| The ADRs' Confirmation checks were missing from later steps | upstream-gap | Steps 8, 11 and 12 patched in PR #54 | Static checks 18, 21, 35; V6.2 |
| Carry-overs: Pyodide smoke test, `FutureWarning` deprecation class and `registry.validate()`, a docs build with warnings as errors and Sybil, the NumPy/SciPy `requires_python` re-check, the milestone-tag check | upstream-gap | Owned by Phase 2 (carry-over list in the phase roadmap) | Phase 2 roadmap |
| ROADMAP §5 wording on the IMF's terms and an OpenBB quote | spec-rot | ROADMAP edited in PR #54 | none (one-off) |
| The transfer to `pyeconomics-dev` dropped `release-tags`' bypass actor | security | Restored by the maintainer | V2.5 checks `release-tags` is active |
| The transfer restarted Dependabot on 0.2.x's workflows (PRs #55–#58) | process | Closed; Step 7 removed the workflows | `.github/dependabot.yml`; V5.4 |
| rdap.org has no `.io` entry | spec-rot | Step 12's RDAP check uses Identity Digital's server | V6.2 |

## Step 7 — Repository reset and package skeleton (PR #59)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| A plain `uv lock` wrote the private firewall index into `uv.lock` and `pylock.toml` | security | Fixed in PR #59 (`--no-config`); Steps 8 and 9 patched | `lock-index` hook; AGENTS.md `--no-config` rule |
| `uv_build` always adds `pyproject.toml.orig` to the sdist | spec-rot | The allowlist admits it when it is byte-identical | `scripts/checks/dist_contents.py`; V7.3 |
| A stale root `pyeconomics.egg-info` can shadow the wheel's metadata | spec-rot | Clean-venv imports run outside the checkout (Steps 7, 10, 12) | `ci.yml` package job; V7.2 |
| Auto mode blocks `git rm` of tracked trees | process | Agent memory; batched approvals | CLAUDE.md |
| `CITATION.cff` was stale | bug | Fixed in PR #67 | Static check 44 |

## Step 8 — Per-step security gate (PR #60)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| The bare `semgrep --test .semgrep/` passes vacuously | spec-rot | Roadmap edited in PR #60 | `semgrep-test` hook; V8.2 |
| gitleaks allowlists AWS's `…EXAMPLE` key, so a gate proof needs gitleaks' own fixture key | spec-rot | Step 8 and V8.3 name gitleaks' `testdata/repos/nogit/main.go` | V8.3 (`--post`) |
| semgrep workers race on `~/.semgrep/settings.yml` on Windows | bug | Fixed in PR #60: one rule at a time | `scripts/checks/semgrep_tests.py` |
| The gate blocked a roadmap commit that quoted a fake key | process | AGENTS.md: refer to a test key by its location | gitleaks hook |
| ruff, mypy, pyright and ty must exclude `.semgrep/tests` | upstream-gap | Step 9's task | `pyproject.toml` excludes |
| No separate gitleaks install is needed | spec-rot | Step 11's task | none (one-off) |
| Step 12 must use `semgrep-test` and skip `no-commit-to-branch` on `main` | upstream-gap | Step 12's task | `verify-phase01.sh --security` |
| VS Code's LSP servers hold `.venv` open on Windows | process | Agent memory | none (editor-local) |
| Scorecard's baseline is 6.4, with seven alerts | security | Issue #62 (open; dispositions recorded, two maintainer decisions pending) | `scorecard.yml` runs weekly |

## Step 9 — Quality toolchain (PR #63)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| An `Iterable` default tested for truthiness is always true for a generator (found by ty) | bug | Fixed in PR #63 (`Collection`) | mypy strict; ty (informational) |
| A stale, git-ignored root `pyeconomics/` directory made coverage report 0% | bug | Fixed in PR #63 (`source_pkgs`) | Coverage config; AGENTS.md `uv run pytest` |
| GitHub misreads typing-extensions' licence and files dev groups as runtime | upstream-gap | dependency-review exemptions by purl (PR #63) | The `licences` hook reads real metadata |
| Every Python file needs the CPY001 header | spec-rot | Step 11's CONTRIBUTING | ruff CPY001 |
| CI must run hooks by id, set `HYPOTHESIS_PROFILE`, keep pyright editor-only | upstream-gap | Step 10's task | `ci.yml` |

## Step 10 — CI/CD and publishing rehearsal (PRs #64, #66)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| The `id-token` criterion left out Scorecard's job | spec-rot | Roadmap edited in PR #66 | Static check 36 (release.yml's two publish jobs) |
| Python 3.15 was not final | process | Issue #65 (open; adds 3.15 at its final release, ADR-0010) | Static check 35: classifiers equal the matrix |
| Dependabot cannot sign off, but `dco` is required | process | Fixed in PR #64: exempt by authenticated PR author | `dco` job |
| CONTRIBUTING's DCO text, check 37's `./` exemption, V7.3's script name | upstream-gap | Steps 11 and 12 patched | Static checks 37, 41; V7.3 |
| `ubuntu-latest` moves to Ubuntu 26 on 2026-10-19 | process | No change needed. `ci.yml` and `phase-verify.yml` run on every push, so the first run after the move tests the new image | `ci.yml`; `phase-verify.yml` |

## Step 11 — Governance, community and agent instructions (PRs #67, #69)

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| A wrongly linked Stripe account blocks the `pyeconomics-dev` GitHub Sponsors listing | process | Issue #68. On 2026-10-08 the maintainer moved it from Step 12 to ROADMAP 8.1 as a Gate G1 carry-over, so Phase 1 closes with thanks.dev live | V11.4 requires the listing once FUNDING.yml names `github:`, and funding.json must match FUNDING.yml |
| Checking the funding profiles needs Sponsors without following redirects, and thanks.dev's API (its pages answer 403) | spec-rot | Roadmap edited in PR #67 | V11.4 |
| The community-profile API shows neither the security policy nor YAML issue forms | spec-rot | Roadmap edited in PR #69 | V11.2 (GraphQL) |
| The repository's About description was stale | bug | Fixed outside the diff (PR #69) | none (one-off) |

## Step 12 — verify-phase01.sh rollup

| Finding | Class | Destination | Guard |
| --- | --- | --- | --- |
| Closed Snyk pull requests still exist (a pull request cannot be deleted), so V5.4 can only check that none is open | spec-rot | V5.4 edited in this step's PR | V5.4 |
| `github.com/OWNER/REPO/community` renders only in a signed-in browser, so V11.2's Issue templates tick cannot be scripted | spec-rot | V11.2 edited in this step's PR: GraphQL `contactLinks` is the scripted proof, and the page tick is manual (seen in Step 11) | V11.2 |
| Under `MSYS_NO_PATHCONV`, native tools read `/tmp/...` as `<drive>:\tmp` | process | The script uses `cygpath -m` for its scratch directory | `verify-phase01.sh` (comment at `TMP`) |
| Windows Python prints CRLF, and `grep -q` under `pipefail` fails a long `curl` feeding it | process | The script strips `\r` and captures pages before matching | `verify-phase01.sh` (`fetch`) |
| The first draft of `phase-verify.yml` quoted a `run:` scalar badly | bug | Fixed before commit; `check-yaml` caught it | `check-yaml` hook |
| `0.2.6.dev1` is yanked on TestPyPI, which is expected after the Step 3 rehearsal; its attestations are still served | process | No change | V2.4 |

### Synthetic alarm (Operations acceptance, V12.5)

`release-smoke.yml` was dispatched by hand on 2026-10-09 00:48 UTC with
`index=testpypi` and `version=0.0.0.dev0`, a version that does not exist. The
run failed at "Install the published version in a fresh venv" with `No
matching distribution found for pyeconomics==0.0.0.dev0`. Nothing was
published.

Synthetic alarm run: https://github.com/pyeconomics-dev/pyeconomics/actions/runs/37866605106

Notification received: the maintainer confirmed on 2026-10-08, in the Step 12
session, that GitHub's failed-run email for this run reached the email address on
their GitHub account. The session's own mail connector reads a different inbox, so
the maintainer's confirmation is the evidence.

## Phase 1 acceptance audit (ROADMAP §4)

Each Phase 1 criterion in the project roadmap is checked against the V-checks. The
evidence is `scripts/verify-phase01.sh --post` on 2026-10-08: 99 checks passed and
none failed (fast 64, python 4, security 3, live 22, post 6).

| ROADMAP criterion | Evidence | Result |
| --- | --- | --- |
| The 0.2.x patch is on PyPI without credential logging, and a published advisory names the affected and fixed versions and the key-rotation advice | Check 6; V4.1, V4.2 (clean install passes `check_credential_logging.py`), V4.3; the advisory text advises rotation | Met |
| The archive tags and `archive/0.2-dev-wip` are on `origin` with the WIP diff intact; `dev/` sits in a private archive with a clean secret scan and an index | Checks 3–5; V5.3; Step 5's scan (PR #53) | Met |
| Characterization fixtures for the four rules are committed | Check 14; V5.2 re-records byte-identically | Met |
| `uv sync --locked` and the full test run pass in CI on three operating systems and every supported Python; `uv build` passes the metadata checks | V10.2 (nine green cells on `main`); V7.2, V7.3 | Met |
| Deployed & verified: `v1.0.0.dev1` on TestPyPI with attestations installs and reports its version; 0.2.6 installs from PyPI; no PyPI API token exists | V10.3 (attestations and clean install), V4.2, V2.5 and V10.5 (no repository secret); the PyPI account has no token (Step 3 readiness §1) | Met |
| A direct push to `main` is rejected; `git branch -r` lists only `main`, `legacy/0.2.x` and archive branches; ADRs 0001–0007, 0009 and 0010 are Accepted | V1.2 (`enforce_admins`, PR required; the push rejection itself was verified in Step 1, PR #46); check 16 (the only other branch is the head of open Dependabot PR #61); check 18 | Met |
| Security: the gate blocks a planted credential and `pickle.loads`; the same checks are required on `main`; zizmor reports nothing above Low; CodeQL and Scorecard run on `main`; secret scanning, push protection and private reporting are on | V8.3; V8.5 and V10.4 (18 required checks, strict); V2.3 and the `zizmor` check; CodeQL and Scorecard green on `main` at `f6b07c6`; V8.4 | Met |

Gate G1 funding hooks: thanks.dev and `funding.json` are live (V11.4). The GitHub
Sponsors listing moved to ROADMAP 8.1 (issue #68), by the maintainer's amendment of
2026-10-08.

## Pre-ship items

Documented limitations:

- `--live` and `--post` need the maintainer's `gh` session and the network, so
  they never run in CI. `--post` re-records the fixtures and installs 0.2.6 from
  PyPI, which takes several minutes.
- Static check 16 needs the GitHub API to list open pull requests' head
  branches. CI passes `GH_TOKEN`. Without `gh`, an open pull request's branch
  fails the check.
- V11.2's Issue templates tick on the community page stays a manual check (Step
  12 rollup above).

Downstream follow-ups, each with its owner:

- Issue #52: record the CVE id for GHSA-j6rp-vwwv-jrr8 when GitHub assigns it
  (`security`; maintainer).
- Issue #62: Scorecard dispositions (`security`). The Code-Review and
  Branch-Protection items wait on the maintainer; the badge belongs to Phase 5
  (5.7).
- Issue #68: the GitHub Sponsors listing and its funding-file entries (`process`).
  ROADMAP 8.1 owns it as a Gate G1 carry-over, by the maintainer's amendment of
  2026-10-08. Do it as soon as GitHub Support detaches the Stripe account.
- Issue #65: Python 3.15 in CI and the classifiers at its final release
  (`process`; ADR-0010).
- Pull request #61: Dependabot's `uv_build` bump predates `ci.yml`. It follows
  the normal review flow after `@dependabot rebase`.
- Phase 2 carry-overs from Step 6, listed above and in the phase roadmap's
  "Not in scope" section.
- `verify-phase02.sh` copies this script's mode contract and appends `"02"` to
  `phase-verify.yml`'s matrix.
