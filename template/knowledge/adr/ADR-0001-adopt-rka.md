---
id: ADR-0001
title: Adopt Repository Knowledge Architecture
status: active
version: 0.1.0
date: 2026-01-01
adr_status: accepted
type: adr
---

# ADR-0001: Adopt Repository Knowledge Architecture

## Context

Project knowledge - decisions, constraints, discoveries - is generated
continuously but usually scattered across commit messages, chat, and stale
docs. Without a home and a lifecycle it rots or is lost.

## Decision

Govern knowledge as a first-class artifact under `knowledge/`, each document
carrying frontmatter with a `status` lifecycle (`draft` → `active` →
`canonical`, or `archived`). Frontmatter is mechanically validated
(`bash scripts/validate-frontmatter.sh knowledge`). This
ADR is itself an example of the pattern.

## Consequences

- Every governed document is discoverable, versioned, and carries an explicit
  trust level via its `status`.
- Promotion to `canonical` requires human review backed by evidence; nothing is
  promoted automatically.
- Contributors must keep frontmatter valid; this project carries no toolchain of
  its own, so wire `scripts/validate-frontmatter.sh` into whatever gate you
  already run (a pre-commit hook, CI, or both).

## Alternatives considered

- **Ad-hoc docs with no lifecycle**: rejected - it's the status quo this
  template exists to replace.
