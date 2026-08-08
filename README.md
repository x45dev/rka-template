# RKA governance template

A [Copier](https://copier.readthedocs.io/) template that drops the Repository Knowledge Architecture (RKA) governance layer into a new or existing repository.
RKA treats a project's durable knowledge as a first-class artifact: decisions, constraints, and discoveries live in versioned documents under `knowledge/`, each carrying a frontmatter `status` that records who may change it and how far to trust it, with promotion to `canonical` gated on human review backed by evidence.
This template ships that layer and nothing else - the seed documents, the entry point for AI coding agents, a dependency-light frontmatter validator, and the validator's own test suite.

## RKA is a profile of OKF

RKA does not compete with [Google Cloud's Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md); it is a **profile** of it (`ADR-0006`).

* **OKF v0.2 is the baseline.** A knowledge bundle is a directory of markdown files with YAML frontmatter. `type` is the one required field. `index.md` and `log.md` are reserved for bundle structure. Conformance is deliberately permissive: a consumer must not reject a bundle for unknown `type` values, unknown keys, missing optional fields, broken cross-links, or a missing index.
* **RKA is what you add on top.** Document identity (`id`, with id/filename conventions), `version`, the ADR shape (`adr_status`), the governed spec-bundle lifecycle, the mandatory constitution, bundle-index integrity, and the extraction-record rule - the things OKF's non-goals put deliberately out of scope.
* **The profile narrows OKF's reserved keys; it never redefines them.** `status` takes OKF's `draft | stable | deprecated`. The trust axis - what RKA calls `canonical` - lives in OKF's `verified`, where a `human:<id>` actor is what confers the human-reviewed tier. That is the mechanism behind "nothing becomes canonical without a human deciding it", and unlike the prose version of that rule, a validator can check it.

An RKA bundle is therefore an OKF bundle, and adopting this template into a repository that already speaks OKF is additive rather than a migration.

> **Status:** `ADR-0006` is *proposed*. The reconciled schema is not yet the shipped one - what ships today still uses RKA's `draft | active | canonical | archived` vocabulary and a `date` field. Until the migration lands, a bundle from this template targets OKF v0.1 rather than v0.2.

## Which template do I want?

| You want | Take |
| --- | --- |
| The knowledge standard, dropped into a repo that already has its own toolchain | **this template** |
| A repository that starts already tooled - mise, lefthook, git-cliff, SOPS, lint gate - with the knowledge layer as one part of it | `github.com/x45dev/workspace-template` |
| A FastAPI + Astro application scaffold as well | the same, with `include_app` |

The two share no commit, so moving between them is a fresh render, never a `copier update`.
(`workspace-template` is deliberately named rather than linked: it is private, so a link resolves to a 404 for most readers of this file.)

## Usage

```bash
copier copy gh:x45dev/rka-template .
```

Run it in a fresh directory for a new project, or at the root of an existing repository to adopt RKA into it.
The template installs no task runner, no lint config, and no CI: wiring the validator into the gate you already have is the adopter's call.

The answers file is `.copier-answers.rka-template.yml`, not Copier's default `.copier-answers.yml`, so adopting this template into a repository that another Copier template already generated leaves that repository's own answers file untouched.
The cost is that `copier update` has to be told the name, because it reads the answers file before it can read the template and so cannot discover it:

```bash
copier update -a .copier-answers.rka-template.yml --vcs-ref v1.2.3
```

**Omitting `-a` in a repository that carries another template's answers file does not fail.**
Copier falls back to `.copier-answers.yml`, finds the other template's `_src_path`, and updates that template instead.

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

1. Render into a scratch directory: `rm -rf /tmp/rka-render && copier copy --vcs-ref <tag> gh:x45dev/rka-template /tmp/rka-render`.
2. Diff it against your repository. The render is fourteen files and every one of them can collide:

   | Path | Collides with |
   | --- | --- |
   | `knowledge/` (`constitution.md`, `context.md`, `PRD.md`, `activeContext.md`, `progress.md`, `adr/ADR-0001-adopt-rka.md`) | any repository that already practises RKA - including every project generated from the predecessor unified template |
   | `scripts/validate-frontmatter.sh`, `tests/validate-frontmatter.bats` | likewise; the predecessor shipped both |
   | `README.md`, `AGENTS.md`, `.gitignore`, `.gitattributes`, `LICENSE` | almost any repository |
   | `.copier-answers.rka-template.yml` | only another install of *this* template |

3. Reconcile by hand, then wire `bash scripts/validate-frontmatter.sh knowledge` into your existing pre-commit or CI gate.

Two traps, both worth reading before you start.

**`copier copy` at your repository root is for a repository that does not already practise RKA.**
Where the paths above collide, Copier stops at the first conflict and writes nothing, then suggests `--overwrite` - which resolves every conflict by discarding your version.
On a repository that already has a governed `knowledge/`, that replaces your constitution, context, PRD and working state with the seed stubs.
The one exception to the stop-and-ask behaviour is the answers file, which Copier always writes without asking; the distinct filename above is what keeps that from taking another template's answers file with it.

**The shipped validator cannot tell you this happened.**
It checks frontmatter, ids, and the lifecycle rules - all of which the seed stubs satisfy, because they are valid RKA documents.
A `knowledge/` overwritten with stubs passes `validate-frontmatter.sh` with exit 0.
`git diff` is the check that catches it, which is why step 2 is a diff and not a copy.

## Consuming this template

**Consume it copy-fresh.**
This template was extracted from a private unified template that also carried an application layer and a tooling preset.
It shares no history with that predecessor and there is no `copier update` path from it: a project generated from the predecessor adopts this template with a fresh `copier copy` and a manual reconcile, not an update.

**If you adopted `v0.1.0`, rename the answers file once.**
That release recorded answers under Copier's default `.copier-answers.yml`, and the update command above cannot find them:

```
Cannot update because cannot obtain old template references from `.copier-answers.rka-template.yml`.
```

Rename it and updates work again; nothing inside the file changes.

```bash
git mv .copier-answers.yml .copier-answers.rka-template.yml
copier update -a .copier-answers.rka-template.yml --vcs-ref <tag>
```

Do this before the first update past `v0.1.0`, and do it whichever order suits you - the rename alone is inert until you update.

**Pin to release tags.**
Update against tags only, so what arrives is a reviewed batch rather than whatever the default branch happens to be:

```bash
copier update -a .copier-answers.rka-template.yml --vcs-ref v1.2.3
```

The rule is advice here rather than a shipped gate.
The predecessor template enforced it with a generated check that lived in its tooling preset; that preset is not part of this template, and re-adding a gate would mean shipping tooling into repositories that chose this template precisely because they have their own (see `knowledge/adr/ADR-0001-extract-the-governance-template.md`).

## The standard itself

The RKA standard - the RFCs, the constitution, and the reasoning behind the lifecycle this template ships - lives at [github.com/x45dev/repository-knowledge-architecture](https://github.com/x45dev/repository-knowledge-architecture).

## Developing this template

This repository governs itself with the standard it ships: its own `knowledge/` is validated in CI by the very script under `template/`.

```bash
bash dev/gates.sh
```

That runs the generation suite, renders the working tree, checks the render's seed `knowledge/` with the render's own validator, checks this repository's `knowledge/` with the *shipped* validator, runs the shipped BATS suite, and rejects em dashes.
CI calls the same script, so the two cannot drift.
Named gates run individually (`bash dev/gates.sh pytest render`), `--ref <ref>` renders a committed ref rather than the working tree, and `--strict` makes a gate that could not run a failure rather than a warning.

Always verify against a rendered project rather than the template source: the render is the step that would silently eat a Jinja construct in a shipped script.

See `AGENTS.md` for the source-versus-instance rule and the traps particular to editing a Copier template.
