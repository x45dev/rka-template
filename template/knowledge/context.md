---
id: context
title: Context
status: draft
version: 0.1.0
date: 2026-01-01
type: context
---

# Context

> The single combined context document: product context, system patterns, and
> technical context together. This is the default starting shape (RFC-003
> section 4, PRD FR1.3) and the extraction target for durable knowledge that is
> not a single decision (which would be an ADR). Split it into named documents
> (`productContext.md`, `systemPatterns.md`, `techContext.md`) only once a
> section grows large enough to earn its own file - adding them before they are
> consumed violates the deletion test. Promote to `active`/`canonical` once
> reviewed.

## Product context

<!-- Why this project exists from the user's side: who it serves, the
     experience it should provide, and the problems it removes for them. -->

## System patterns

<!-- Recurring architectural patterns, structural conventions, and discovered
     constraints that shape how the system is built. Record a pattern here once
     it has proved itself, rather than losing it to history. -->

## Technical context

<!-- The technical environment: languages, tools, key dependencies provisioned
     via your own toolchain, and the technical decisions behind them (the *why* behind the
     stack, distinct from an ADR's single decision). -->
