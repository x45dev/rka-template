---
id: activeContext
title: Active Context
status: active
version: 0.1.1
date: 2026-07-31
type: context
---

# Active Context

Current focus and the immediate to-do for this repository.
Working state lives here, never in the README or the PRD.

## Current focus

The template has just been extracted from its predecessor and committed as a fresh repository with no history and no remote.
The generation suite, a rendered project's own gates, and self-governance all pass locally.

## Decisions in flight

- **The public repository identity is not settled.**
  The local working name is `rka-template-governance`; the README and `copier.yml` documentation both assume the published identity will be `gh:x45dev/rka-template`, on the expectation that the name is handed over from the predecessor.
  If that handover does not happen, the usage line in `README.md` is the one place that has to change.
- **Whether the pin-to-tags rule ever becomes mechanical here.**
  ADR-0001 records it as advice, on the reasoning that a gate is a tooling concern.
  Revisit only if adopters are observed drifting off tags in practice.

## Next steps (to-do)

- [ ] Decide the published repository name and reconcile the usage line in `README.md` with it.
- [ ] Create the remote, push, and cut the first release tag so adopters have something to pin to.
- [x] Verify the shipped validator against the Python yq flavour as well as the Go one. An adversarial review exercised it under kislyuk yq 4.1.2: the capability probe correctly rejected `-o=json`, execution fell to the bare-yq branch, and the validator exited 0 over this repository's own `knowledge/`.
- [ ] Write the consumer-facing migration note for projects moving off the predecessor unified template.
