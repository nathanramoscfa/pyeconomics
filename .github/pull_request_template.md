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
