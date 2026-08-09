---
id: PRD
title: Product Requirements Document
status: canonical
version: 0.3.2
date: 2026-08-09
type: prd
---

# Product Requirements Document

This is the PRD for **the template itself**, not for a project generated from it.

## 1. Introduction

The RKA governance template is a single-purpose Copier template.
It delivers the Repository Knowledge Architecture governance layer into a new or existing repository and carries no other layer.

RKA's governed `knowledge/` is a **conformant OKF v0.1 bundle** (`repository-knowledge-architecture` ADR-0011). Three 2026-08 proposals to retarget it to v0.2 were reviewed and none accepted.
OKF is the baseline: a directory of markdown files with YAML frontmatter, `type` as the one required field, `index.md` and `log.md` reserved for bundle structure, and permissive conformance that forbids rejecting a bundle for unknown types, unknown keys, missing optional fields, broken links, or a missing index.
The profile adds identity, versioning, the ADR and spec-bundle shapes, the mandatory constitution, bundle-index integrity, the extraction-record rule, and the human-gated promotion discipline - the things OKF's non-goals put out of scope.
RKA's own keys ride as OKF extension keys, which conformant consumers preserve; RKA does not redefine keys OKF specifies.

## 2. Goals

- Let a repository adopt RKA without adopting a toolchain, a lint preset, or CI configuration alongside it.
- Keep the profile strictly additive to the OKF baseline, so a repository that already speaks OKF adopts RKA without migrating away from anything, and a repository that adopts RKA gets OKF conformance for free.
- Make the render safe to run at the root of an existing repository.
- Keep the shipped validator runnable on a machine that has only bash, awk, yq and jq.
- Prove, in this repository's own CI, that the standard being shipped is the standard being practised.

## 3. Requirements

### Functional

- **FR1** A default render emits exactly: `knowledge/` (constitution, context, PRD, activeContext, progress, and a seed ADR), `scripts/validate-frontmatter.sh`, `tests/validate-frontmatter.bats`, `AGENTS.md`, `README.md`, `.gitignore`, `.gitattributes`, `.copier-answers.rka-template.yml`, and `LICENSE` unless the license answer is Proprietary.
- **FR2** Six questions are asked: project name, project slug, description, author name, license, and copyright year.
- **FR3** A `project_name` that sanitizes to an empty slug fails generation rather than emitting an illegal directory name.
- **FR4** The shipped validator enforces the RKA frontmatter schema, the id and filename conventions, the constitution's presence, the optional bundle index, and the spec-bundle lifecycle rules.
- **FR5** `AGENTS.md` carries no frontmatter and is not a governed document.
- **FR6** A generated project carries a committed answers file, so `copier update` can re-apply later template evolution.
- **FR7** Adoption into a repository that another Copier template already generated leaves that repository's `.copier-answers.yml` untouched; this template records its answers under a distinct name (ADR-0004).

### Non-functional

- **NFR1** Generation invokes no external tool beyond Python and Copier.
- **NFR2** The generation suite runs in seconds on a machine with only Python, Copier, pytest and PyYAML.
- **NFR3** A `project_name` containing quotes, apostrophes, ampersands, angle brackets, or backslashes renders a project whose YAML still parses and whose frontmatter still validates.

## 4. Out of scope

- Any application scaffold.
- Any task runner, lint, formatter, or CI configuration in the render.
- A mechanical pin-to-tags gate in consumers.
- An update path from the predecessor unified template.
