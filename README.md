# RKA governance template

A [Copier](https://copier.readthedocs.io/) template that drops the Repository Knowledge Architecture (RKA) governance layer into a new or existing repository.
RKA treats a project's durable knowledge as a first-class artifact: decisions, constraints, and discoveries live in versioned documents under `knowledge/`, each carrying a frontmatter `status` that records who may change it and how far to trust it, with promotion to `canonical` gated on human review backed by evidence.
This template ships that layer and nothing else - the seed documents, the entry point for AI coding agents, a dependency-light frontmatter validator, and the validator's own test suite.

## Usage

```bash
copier copy gh:x45dev/rka-template .
```

Run it in a fresh directory for a new project, or at the root of an existing repository to adopt RKA into it.
The template installs no task runner, no lint config, and no CI: wiring the validator into the gate you already have is the adopter's call.

## Prerequisites

The validator is deliberately dependency-light, and the template assumes you already have a toolchain of your own.

| Tool | Needed for | Notes |
| --- | --- | --- |
| `bash` | the validator | 4.x or later (associative arrays) |
| `awk` | the validator | any POSIX awk |
| `yq` | the validator | either flavour: [mikefarah/yq](https://github.com/mikefarah/yq) (Go) or [kislyuk/yq](https://github.com/kislyuk/yq) (Python) |
| `jq` | the validator | |
| `bats` | the shipped test suite | install via `apt install bats`, `npm install -g bats`, or a `bats-core` clone; it is **not** a pip package |
| `copier` | generation and updates | `pip install copier` or `uv tool install copier` |

## Brownfield adoption

Adopting into a repository that already has content is a diff-and-copy, not a blind overwrite.

1. Render into a scratch directory: `copier copy --vcs-ref <tag> gh:x45dev/rka-template /tmp/rka-render`.
2. Diff it against your repository and reconcile by hand where the two overlap - most commonly `README.md`, `AGENTS.md`, and `.gitignore`, which are yours after the first copy.
3. Copy across what is genuinely new (`knowledge/`, `scripts/validate-frontmatter.sh`, `tests/validate-frontmatter.bats`) plus the `.copier-answers.yml` the render produced, then wire `bash scripts/validate-frontmatter.sh knowledge` into your existing pre-commit or CI gate.

## Consuming this template

**Consume it copy-fresh.**
This template was extracted from a private unified template that also carried an application layer and a tooling preset.
It shares no history with that predecessor and there is no `copier update` path from it: a project generated from the predecessor adopts this template with a fresh `copier copy` and a manual reconcile, not an update.

**Pin to release tags.**
Update against tags only, so what arrives is a reviewed batch rather than whatever the default branch happens to be:

```bash
copier update --vcs-ref v1.2.3
```

The rule is advice here rather than a shipped gate.
The predecessor template enforced it with a generated check that lived in its tooling preset; that preset is not part of this template, and re-adding a gate would mean shipping tooling into repositories that chose this template precisely because they have their own (see `knowledge/adr/ADR-0001-extract-the-governance-template.md`).

## The standard itself

The RKA standard - the RFCs, the constitution, and the reasoning behind the lifecycle this template ships - lives at [github.com/x45dev/repository-knowledge-architecture](https://github.com/x45dev/repository-knowledge-architecture).

## Developing this template

This repository governs itself with the standard it ships: its own `knowledge/` is validated in CI by the very script under `template/`.

```bash
python3 -m pytest tests/ -q                        # generation invariants
copier copy --defaults . /tmp/rka-render --trust   # render the template

# the render's own seed knowledge, checked by the render's own validator
(cd /tmp/rka-render && bash scripts/validate-frontmatter.sh knowledge)

# this repository's knowledge, checked by the SHIPPED validator from the render
bash /tmp/rka-render/scripts/validate-frontmatter.sh knowledge

bats /tmp/rka-render/tests/validate-frontmatter.bats   # shipped test suite
```

Always verify against a rendered project rather than the template source: the render is the step that would silently eat a Jinja construct in a shipped script.

See `AGENTS.md` for the source-versus-instance rule and the traps particular to editing a Copier template.
