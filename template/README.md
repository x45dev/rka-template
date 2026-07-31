# {{ project_name }}

{{ description }}

This repository is governed by **Repository Knowledge Architecture (RKA)**:
project knowledge lives under `knowledge/`, each document carries a `status`
lifecycle, and that governance is mechanically validated.

## Getting Started

This project carries the governance layer only - no task runner is assumed, and
no tool configuration is installed. Wire the validator into whatever you
already use:

```bash
bash scripts/validate-frontmatter.sh knowledge
```

It depends only on `bash`, `awk`, `yq` and `jq`. Its own test suite runs with
[bats](https://bats-core.readthedocs.io/):

```bash
bats tests/validate-frontmatter.bats
```

## Knowledge lifecycle

Every governed document in `knowledge/` carries frontmatter with a `status`
(the reserved `index.md` and `log.md` are exempt):

| Status | Permission | Trust |
| --- | --- | --- |
| `draft` | freely editable | unverified |
| `active` | freely editable | working trust; rely with caution |
| `canonical` | review-gated | authoritative |
| `archived` | immutable | retired; preserved for provenance |

Nothing becomes `canonical` automatically - promotion requires human review
backed by evidence. `bash scripts/validate-frontmatter.sh knowledge` checks that
every governed document has valid frontmatter (required fields, a legal status,
a unique id).

### Feature specs

A feature specification is a governed **bundle** at
`knowledge/specs/<NNN>-<slug>/`: `spec.md` (required) plus optional `plan.md`
and `tasks.md`. The three documents share one `status` and move through the
lifecycle together, and their ids are `<role>-<NNN>-<slug>` (for example
`spec-003-search`) rather than the filename stem, because they share a
directory.

Two rules are enforced mechanically, so a shipped spec cannot be quietly
abandoned:

* An **archived** document must carry an `## Extraction record` section. In a
  bundle that record lives once, in `spec.md`, and covers all three.
* A bundle whose `tasks.md` has at least one checkbox and **no unchecked
  checkbox must be `archived`**. Ticking the final box is therefore a
  commit-time cliff: extract the durable knowledge into its permanent home,
  record where it went, and archive the bundle in that same change.

`tasks.md` is optional; a bundle without one is never subject to the second
rule.

`AGENTS.md` is the entry point for AI coding agents working in this repository.
The RKA standard itself lives at
[github.com/x45dev/repository-knowledge-architecture](https://github.com/x45dev/repository-knowledge-architecture).

## Where things go

Keep working-state out of the README and the PRD - they are durable documents.

| Document | Holds |
| --- | --- |
| `knowledge/constitution.md` | Why the project exists, invariants, hard constraints, Definition of Done, non-goals |
| `knowledge/context.md` | Combined product context, system patterns, and technical context. Split into named files only once a section earns its own |
| `knowledge/activeContext.md` | Current focus, decisions in flight, **to-do** |
| `knowledge/progress.md` | What works, what's left, known issues |
| `knowledge/PRD.md` | Durable product requirements |
| `knowledge/adr/` | Architecture Decision Records |

## Updating from the template

This repo was generated from the RKA governance template and carries a committed
`.copier-answers.yml`. Pull later template evolution in with:

```bash
copier update           # re-applies template changes via a three-way merge
```

Update against release tags only, so what arrives is a reviewed batch rather
than whatever the template's default branch happens to be:

```bash
copier update --vcs-ref v1.2.3
```
