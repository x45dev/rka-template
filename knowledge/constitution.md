---
id: constitution
title: Constitution
status: canonical
version: 0.1.0
date: 2026-07-31
type: constitution
---

# Constitution

*This constitution governs the template repository itself, not a project generated from it.*

## Why this project exists

This repository is a Copier template that delivers the Repository Knowledge Architecture governance layer, and nothing else, to a new or existing repository.
It exists so that a project can adopt RKA without also adopting somebody else's toolchain.
The predecessor template bundled governance with a task runner, a lint preset, and an application scaffold; adopting the standard meant taking all three or hand-extracting the part you wanted.

## Invariants

These must hold whatever else changes.

- **The render is the governance layer and nothing else.**
  No task-runner config, no lint preset, no CI workflow, no application code.
  A consumer already has those, and overwriting them is the failure this template exists to avoid.
- **Generation shells out to nothing.**
  A bare Python and Copier machine renders successfully; generation never invokes a package manager or a task runner.
- **The shipped validator depends only on bash, awk, yq and jq.**
  Either yq flavour, probed by capability rather than by version string.
- **This repository obeys the standard it ships.**
  Its own `knowledge/` is validated in CI by the very script under `template/`.
- **Shipped markdown carries no em dash.**

## Hard constraints

- Every file under `template/` renders with default Jinja delimiters, so a shipped script containing `{` followed by `#` has its code silently deleted at render time.
  This is a property of the engine, not a style preference.
- Copier's `_skip_if_exists` is write-once, so it cannot be used to protect a consumer's pre-existing file: a file listed there is never updated again.
  Consumer-owned files are reconciled by three-way merge instead.
- The template shares no history with its predecessor, so `copier update` cannot carry a project across.

## Definition of done

A change is done when the generation suite passes, a rendered project passes the shipped validator and the shipped BATS suite, this repository's own `knowledge/` passes the shipped validator, and the durable knowledge from the change has been extracted into an ADR or `context.md`.

## Non-goals

- Distributing a toolchain, a lint preset, or CI configuration.
- Shipping an application scaffold.
- Mechanically enforcing the pin-to-tags update rule in consumers; that gate belongs to a tooling preset, not to the standard.
- Providing an upgrade path from the predecessor unified template.
