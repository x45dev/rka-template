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

Run these locally before you consider a change done.

| Gate | Command |
| --- | --- |
| generation invariants | `python3 -m pytest tests/ -q` |
| render (working tree) | `rm -rf /tmp/rka-src /tmp/rka-render && mkdir /tmp/rka-src && cp -a copier.yml template /tmp/rka-src/ && copier copy --defaults --trust /tmp/rka-src /tmp/rka-render` |
| render (a committed ref) | `rm -rf /tmp/rka-render && copier copy --defaults --trust --vcs-ref HEAD . /tmp/rka-render` |
| shipped validator, over the render | `(cd /tmp/rka-render && bash scripts/validate-frontmatter.sh knowledge)` |
| self-governance | `bash /tmp/rka-render/scripts/validate-frontmatter.sh knowledge` from this repo's root |
| shipped BATS suite | `bats /tmp/rka-render/tests/validate-frontmatter.bats` (see the prerequisites table in `README.md` if `bats` is absent) |
| em dash | `grep -rPn '\x{2014}' --include='*.md' .` must find nothing |

Always verify against a `copier copy`-rendered project, never the template source: the render is the step that would silently eat a `{#`.

**Never render with a bare `copier copy ... .`.**
Copier's default ref for a git template is its latest *tag*, so that command renders the last release and every gate below it then reports on code you did not write.
This repository is tagged, so the trap is live on any full clone.
Render from the plain copy while you are working - it is the only form that sees uncommitted edits, and it is what `tests/conftest.py` does - and pin `--vcs-ref HEAD` once the work is committed.

**Clear the render directory before every render**, which is why both rows above open with `rm -rf`.
Copier reads an existing `/tmp/rka-render` as an update, conflicts on the first file that differs, and in a non-interactive shell exits 1 having written nothing.
The three rows beneath it are separate commands, so they then examine the render from last time and pass - the same trap as the bare `.` render, reached by a different route.
`tests/test_gate_invocations.py` holds both properties over these rows, because a gate procedure delivered as prose has no other gate.

**A gate you could not run is not a gate that passed.**
`bats` in particular is absent from many machines and is not a pip package; where a tool is missing, say which gate did not run rather than reporting the rest as green.
