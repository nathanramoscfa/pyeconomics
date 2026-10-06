# ADR-NNNN: Title in a few words

- Status: Proposed
- Date: YYYY-MM-DD
- Deciders: Nathan Ramos, CFA (maintainer)
- Parent: the ROADMAP section this decision implements

## Context and problem

What forces a decision now, and what goes wrong without one. State the facts
the decision rests on. Any fact that can change (a release date, a version
floor, a licence, a price, whether a name is available) carries a source in
"More information" with its access date, or reads TBD. Never guess.

## Decision drivers

- The constraints and goals the options are judged against, most important
  first.

## Considered options

1. **The chosen option.** One paragraph.
2. **An alternative.** One paragraph, including why it lost.

## Decision outcome

Chosen option: **…**, because … (tie it back to the drivers).

The decision itself, stated as rules a later step can follow without
re-arguing it.

### Consequences

Good:

- What becomes easier or safer.

Bad:

- What it costs, what it rules out, and what must be watched.

### Confirmation

The check that enforces this decision, and the roadmap step that builds it.
For example: "`requires-python` in `pyproject.toml` (Phase 1 Step 7) and the
CI matrix (Phase 1 Step 10)". A decision with no enforcing check names the
review that stands in for one.

## More information

- Related ADRs and roadmap sections.
- Sources for every time-sensitive fact, as `[Sn] <URL>, accessed
  YYYY-MM-DD`, cited inline as [Sn].
- Amendments made before acceptance, each with its date.
