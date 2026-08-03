---
id: activeContext
title: Active Context
status: active
version: 0.1.3
date: 2026-08-03
type: context
---

# Active Context

Current focus and the immediate to-do for this repository.
Working state lives here, never in the README or the PRD.

## Current focus

The template is published at `github.com/x45dev/rka-template` and `v0.1.0` is tagged on the remote, so adopters have something to pin to.
CI is green on that commit, and the generation suite, a rendered project's own gates, and self-governance all pass locally.
Everything the extraction set out to do is done; what completed is recorded in `progress.md`, which is where this repository's output belongs.
The seed documents were promoted to `canonical` by the owner on 2026-08-03; the evidence and what the promotion covers are in `progress.md`.

## Decisions in flight

- **Whether the pin-to-tags rule ever becomes mechanical here.**
  ADR-0001 records it as advice, on the reasoning that a gate is a tooling concern.
  Revisit only if adopters are observed drifting off tags in practice.

## Next steps (to-do)

None open.
The next work here is reactive: an adopter's report, or a change to the RKA standard that moves the shipped schema.

`v0.1.0` is now behind the working tree in a way that matters to adopters: it ships the contested answers filename and the flagless update command.
Cutting the next tag is what makes ADR-0004 reach anyone, and until then the README on the default branch documents behaviour that the released tag does not have.
That tag carries a breaking change for `v0.1.0` adopters - the answers filename - so its release notes should lead with the one-line `git mv` migration in `README.md` rather than bury it in a file list.

## Naming the predecessor

The predecessor unified template is a private repository.
This one is public, so its documents describe the predecessor by role and never by name: naming it would publish the existence and identity of a private repository to anyone reading the template.
That constraint is why every reference here and in `README.md` reads "the predecessor unified template", and it is a constraint rather than a stylistic habit.
