# AGENTS.md

You are working on the **RKA governance template**: a Copier template that distributes the Repository Knowledge Architecture governance layer to consuming projects.
This repository is a template first and a project second, and most mistakes here come from confusing the two.

## 1. Source vs instance

* Everything a generated project receives lives under `template/`.
  Edit the source under `template/`, never a rendered instance in a consumer repo, or the change is lost on the next `copier update`.
* Every file under `template/` is rendered with default Jinja delimiters (`_templates_suffix: ""`).
  A shipped script must not contain `{` immediately followed by `#` - that is the Jinja comment open, and bash parameter-count expansions are the classic way to introduce it by accident.
  It has two failure modes: with no later `#}` the render aborts with "Missing end of comment tag", and *with* a later `#}` the render succeeds silently with everything between the two deleted.
  The second is why `tests/test_generation.py` greps the template SOURCE rather than the render - by the time output exists, the evidence is gone.
  Grep shipped scripts for `{#`, bare `{{`, and bare `{%` before committing.
* This template carries the governance layer only.
  A file that assumes a task runner, a lint preset, or a CI workflow does not belong under `template/`; the exact render shape is pinned by `test_render_is_the_governance_layer_and_nothing_else`.
* The root `knowledge/` is this repository's OWN governed knowledge, not a rendered artifact.
  CI runs the shipped validator against it, so a change to the shipped frontmatter schema and the matching migration of this repository's own documents land in the same change.
* Root `tests/` is the template's generation harness (pytest), not shipped content.
  `template/tests/` is the shipped BATS suite.

## 2. Governance for this repository's own knowledge/

* `knowledge/` documents carry six-field RKA frontmatter (`id`, `title`, `status`, `version`, `date`, `type`).
  ADRs additionally carry `adr_status` and no prose `## Status` section.
* Nothing becomes `canonical` without a human deciding it.
  You may author a promotion and furnish the evidence for it; you never record one.
* Working state lives in `knowledge/activeContext.md` and `knowledge/progress.md`, never in the README or the PRD.
* Before archiving any document, extract the durable knowledge first - a single decision becomes an ADR, anything else goes to `knowledge/context.md` - then archive.
* Shipped and repo-level markdown carries no em dash (U+2014); CI greps for it.

## 3. Gates

Run this locally before you consider a change done.

```bash
bash dev/gates.sh
```

It is the same code CI runs.
Individual gates take their names as arguments (`bash dev/gates.sh pytest render`), `--ref <ref>` renders a committed ref instead of the working tree, and `--strict` turns a gate that could not run into a failure.

| Gate | What it checks |
| --- | --- |
| `pytest` | generation invariants |
| `render` | the working tree renders; the source every gate below reads |
| `validate-render` | the render's seed `knowledge/`, by the render's own validator |
| `validate-self` | this repository's `knowledge/`, by the *shipped* validator |
| `bats` | the shipped BATS suite |
| `em-dash` | no U+2014 in any markdown |

**Do not restate these commands here or anywhere else.**
They used to be written out in this table, twice in `README.md` and twice in the workflow, with a test that parsed them back out of the prose to check the copies had not drifted.
Three rounds of adversarial review found twelve holes in that parser and none in the documents, which is what a guard over prose does: it fails silently, because a hole in it reads exactly like a document with no defect.
`dev/gates.sh` holds the commands once and CI calls it, so the copies cannot disagree because there are none (ADR-0005).
`tests/test_gate_invocations.py` is now a few small checks that this arrangement still holds, not a parser.

Two traps are closed inside the script, and both are worth knowing because each cost a session to find.

**A bare `copier copy ... .` renders the latest *tag*, not your work.**
This repository is tagged, so the trap is live on any full clone, and every gate chained off such a render reports on the last release while passing.
The script renders the working tree through a plain directory copy, which is the only form that sees uncommitted edits and is what `tests/conftest.py` does.

**Copier reads an existing destination as an update.**
It conflicts on the first changed file and exits non-zero having written nothing, so a second render leaves the first one in place for the later gates to read.
The script clears the destination first.

Always verify against a rendered project, never the template source: the render is the step that would silently eat a `{#`.

**A gate you could not run is not a gate that passed.**
`bats` is absent from many machines and is not a pip package, so the script names any gate that did not run instead of counting it green.
Repeat that summary as it stands rather than describing the rest as passing.
