---
id: ADR-0003
title: Ship an ungoverned AGENTS.md entry point, deferring to the README
status: draft
version: 0.1.0
date: 2026-07-31
adr_status: accepted
type: adr
---

# ADR-0003 - Ship an ungoverned AGENTS.md entry point, deferring to the README

## Context

This decision is carried forward from the predecessor unified template, where it was recorded as its ADR-0013.
It is restated here because the generation suite enforces one of its clauses, so the reasoning has to be readable next to the test.

A governance project generated from the predecessor received `knowledge/`, a `status` lifecycle and a validator with nothing telling an AI coding agent that any of it existed.
The agent discovered RKA by tripping over a failing gate.

One constraint shaped the file more than the requirement did, and it was found by running things rather than by reading documentation.
**Copier's `_skip_if_exists` is write-once.**
It was the obvious protection for a consumer who already owns an `AGENTS.md`, and it is wrong here.
On copier 9.17.0 a file listed there is never updated again once it exists in the destination: a greenfield project that received the file, a project whose owner edited it, and a brownfield project that already had one all kept their version across a template release, while a control file in the same run updated correctly.
The flag would have frozen the RKA guidance in every existing project permanently.

## Decision

Ship `AGENTS.md` at the root of every generated project as an **ungoverned** document that **defers to the README**.

1. **Ungoverned, and outside `knowledge/`.**
   The validator walks `knowledge/` only, and an RKA id must equal its filename stem, which `AGENTS.md` is not.
   The generation suite asserts the file carries no frontmatter, so a later move under `knowledge/` fails in this repository's tests rather than in a consumer's gate.
2. **Defer, do not restate.**
   `template/README.md` already documents the lifecycle and what belongs in which document.
   The entry point points at it and carries only what the repository does not already show: the one rule no gate enforces (only a human records a promotion to `canonical`), the extraction habit, and an instruction to match surrounding conventions.
3. **Link to the standard normally.**
   The predecessor wrote the standard's URL as a non-clickable code span, because its shipped link gate ran unauthenticated over every markdown file and the standard's repository was private, so an autolink returned 404 and reddened the gate in every generated project.
   Neither half of that constraint applies here: this template ships no link gate at all, and the standard is reachable.
   The URL is a real markdown link in both `AGENTS.md` and `README.md`.
4. **Treat the file as consumer-owned after delivery**, exactly like `README.md`: three-way merge plus release notes, with no `_skip_if_exists`.

## Consequences

- An agent starting in a generated project learns the governance model from the repository rather than from a failing gate.
- The file is short by design.
  Current evidence is that agent instruction files carrying content the repository already shows measurably reduce task success and raise cost, so length here is a cost, not thoroughness.
  An earlier draft in the predecessor that restated the README's two tables had already diverged from them on two of the four statuses before review; the omission is the fix.
- A consumer who already owns an `AGENTS.md` gets a merge conflict on update, which is the intended behaviour and belongs in the release notes as a numbered step.
  It is the same exposure `README.md` has always carried.
- No `CLAUDE.md` symlink ships.
  Copier does not preserve symlinks without `_preserve_symlinks`, and consumers may not use Claude Code at all.

## Alternatives considered

**Protect a pre-existing consumer `AGENTS.md` with `_skip_if_exists`.**
Rejected on the test above: write-once semantics mean no later fix to the RKA guidance ever reaches an existing project, and it would introduce a second pattern for consumer-authored files alongside the three-way-merge one every other such file already uses.

**Restate the lifecycle and where-things-go tables in the entry point.**
Rejected as a second source of truth.
The drafted version in the predecessor had already drifted from the README before anyone read it, which is the failure mode in miniature.

**Put the entry point under `knowledge/` so it is governed like everything else.**
Rejected.
An agent looks for `AGENTS.md` at the repository root, and the id-equals-stem rule would force a rename that defeats the convention.
The generation suite pins the file's ungoverned shape so the question cannot be reopened by accident.

**Ship a `CLAUDE.md` symlink alongside.**
Rejected: it needs a `_preserve_symlinks` change to `copier.yml` and assumes a specific agent, where the file's whole purpose is to be the agent-agnostic entry point.
