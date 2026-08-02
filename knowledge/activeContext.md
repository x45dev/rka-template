---
id: activeContext
title: Active Context
status: active
version: 0.1.2
date: 2026-08-02
type: context
---

# Active Context

Current focus and the immediate to-do for this repository.
Working state lives here, never in the README or the PRD.

## Current focus

The template is published at `github.com/x45dev/rka-template` and `v0.1.0` is tagged on the remote, so adopters have something to pin to.
CI is green on that commit, and the generation suite, a rendered project's own gates, and self-governance all pass locally.
Everything the extraction set out to do is done; what completed is recorded in `progress.md`, which is where this repository's output belongs.

## Decisions in flight

- **Promotion of the seed documents to `canonical` is unmade.**
  The constitution, context, PRD, and all three ADRs sit at `status: draft` while their `adr_status` is already `accepted`, which is the state the first release was cut in.
  Promotion is the owner's to record and never an agent's; the evidence for it is a green CI run against the shipped validator plus the ADRs having survived a release unamended.
- **Whether the pin-to-tags rule ever becomes mechanical here.**
  ADR-0001 records it as advice, on the reasoning that a gate is a tooling concern.
  Revisit only if adopters are observed drifting off tags in practice.

## Next steps (to-do)

None open.
The next work here is reactive: an adopter's report, a change to the RKA standard that moves the shipped schema, or the owner recording the promotion above.

## Naming the predecessor

The predecessor unified template is a private repository.
This one is public, so its documents describe the predecessor by role and never by name: naming it would publish the existence and identity of a private repository to anyone reading the template.
That constraint is why every reference here and in `README.md` reads "the predecessor unified template", and it is a constraint rather than a stylistic habit.
