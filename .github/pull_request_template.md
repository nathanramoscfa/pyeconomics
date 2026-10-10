## Roadmap step

<!-- The phase and step this pull request implements, with a link to its
section in docs/roadmap/, or "none" for a fix or chore outside the roadmap. -->

## Summary

<!-- What changes and why, in a few sentences. -->

## Test plan

<!-- The commands you ran and what they showed. -->

## Screenshots

<!-- For a visible UI change: before and after. Otherwise "n/a". -->

## Breaking changes

<!-- "none", or what breaks for whom and how to migrate. -->

## Rollback plan

<!-- Name the ROADMAP §5 "Rollback" row this change uses (PyPI package,
Documentation, Static site, API, Snapshot job, Database, Excel add-in) and how
you would run it, or "revert the squash commit" when nothing is deployed. -->

## Licence check

- [ ] This pull request adds no runtime dependency and no data source, or each
      one is listed here with its licence, passes the ADR-0004 allowlist (the
      `licences` hook) and fits ROADMAP §5 "Data licensing policy".

## Model checklist

<!-- For a pull request that adds or changes a catalog model. Otherwise write
"not a model pull request" and leave the boxes unticked. The rules are in
CONTRIBUTING "Model definition of done" and tests/golden/README.md. -->

- [ ] The id is final, permanent and in its domain (ADR-0003).
- [ ] `registry.validate()` passes.
- [ ] At least three cited golden cases including an edge case, or a recorded
      `min_cases_reason`.
- [ ] A property test marked `invariant` for each invariant the model declares.
- [ ] `oracle` tests where an independent library exists.
- [ ] Every new source is listed in this body, with its kind and locator.
- [ ] No CFA Program curriculum content: no reading, learning outcome, practice
      problem or worked example.
- [ ] The model card renders.

## Sensitive-data checklist

- [ ] No key, token, secret or password reaches a log, manifest, cache,
      exception message or export.
- [ ] No licensed data in fixtures, notebooks or notebook outputs.
- [ ] No secret in a client bundle.
- [ ] Every new credential, token scope and workflow permission is
      least-privilege.
- [ ] Workflow changes reviewed: actions pinned to a commit SHA,
      `permissions: {}` at the top with per-job grants,
      `persist-credentials: false`, no `pull_request_target`, zizmor clean.

## Security gate bypass

none

<!-- Leave "none", or replace it with the hook you skipped (SKIP= or
--no-verify), the commit, and why it could not wait. -->
