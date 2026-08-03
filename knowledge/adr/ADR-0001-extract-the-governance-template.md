---
id: ADR-0001
title: Extract the governance layer as a standalone template
status: canonical
version: 0.1.0
date: 2026-07-31
adr_status: accepted
type: adr
---

# ADR-0001 - Extract the governance layer as a standalone template

## Context

This repository was extracted from a private unified Copier template that carried three layers behind toggles: an RKA governance layer, an x45dev tooling preset (mise, lefthook, git-cliff, and a shell, YAML and prose lint gate under `.config/`), and a FastAPI plus Astro application layer.
The extraction source was that repository at commit `75a85821857b14adb758065802a4030a6ed5ac7e`.

The unified template already supported the governance-only render through a `include_tooling: false` answer, so the capability being extracted is not new.
What the toggle could not fix is what the template *is*.
A template whose default render carries an application scaffold and a toolchain preset is not a credible distribution channel for a standard: an adopter reads the repository before running it, and what they read is somebody else's stack.
The toggle also had a maintenance cost paid on every change - twelve questions, cross-layer validators, a seven-combination generation matrix, and live `{% if include_tooling %}` branches inside shipped files - all of it borne by a render that uses none of it.

The unified template remains private and continues to serve its own purpose.
This is a split, not a migration.

## Decision

Extract the governance layer into a standalone public template with no layer toggles.

1. **Governance only, no toggles.**
   Six questions remain (project name, project slug, description, author name, license, copyright year).
   The twelve layer and application questions are dropped.
   The render shape is pinned by an exact-file-set assertion, so an extra file arriving is a test failure rather than a silent regression.
2. **Conditional path segments become plain directories.**
   Copier drops a file whose path segment renders empty.
   `template/{% if include_governance %}knowledge{% endif %}/` left in place once the question is gone would render an empty segment and the whole tree would vanish silently, so every such segment was flattened.
   Only `LICENSE` keeps a conditional path, gated on the still-live `license` answer.
3. **Live Jinja branches inside carried files were collapsed deliberately, not left to undefined-variable behaviour.**
   Four files carried `{% if include_tooling %}` branches: the validator's yq-missing hint, the BATS suite's header comment, the seed ADR-0001, and the seed `context.md`.
   Jinja treats an undefined name as falsy, so leaving them would have *happened* to select the right branch while leaving the reader unable to tell intent from accident.
   Each was collapsed to the no-tooling branch by hand and the tree was then grepped for surviving `{%`.
4. **The pin-to-tags enforcement script is dropped.**
   The predecessor shipped `.config/checks/pin-to-tags.sh`, a generated gate asserting that a consumer's `.copier-answers.yml` `_commit` names a release tag.
   It lived in the tooling preset, and the whole point of this template is not to ship a tooling preset.
   Consumers are advised to pin to tags in the README instead.
   Enforcement is a preset's job; the standard's job is to say what the rule is.
5. **This repository governs itself.**
   Its own `knowledge/` is validated in CI by the validator rendered from `template/`, so a change to the shipped frontmatter schema and the migration of this repository's own documents must land in the same change.
6. **Migration from the unified template is copy-fresh only.**
   This repository has fresh history and shares no commit with its source, so `copier update` cannot carry a project across.
   A project generated from the predecessor adopts this template with a new `copier copy` and a manual reconcile.
7. **The name is handed over, not settled here.**
   The local working name is `rka-template-governance`; the intent is that the published identity is `gh:x45dev/rka-template`, with the predecessor retaining its private role under another name.
   That handover is a later gate, and until it is taken the usage line in `README.md` is the single place that records the assumption.

## Consequences

- An adopter reads a repository that is about the standard, and runs a render that touches only the governance layer.
- The generation matrix collapses from seven toggle combinations to one shape, and the questions from eighteen to six, so a change to the shipped standard is cheap to make and cheap to verify.
- The predecessor and this template now both carry the governance layer, and a change to the standard has to be made twice or the two drift.
  This is the real cost of the split and it is accepted knowingly; the alternative was one repository that could not credibly be either thing.
- Consumers get no mechanical pressure to stay on release tags.
  A consumer who updates against a branch will find out when the change surprises them, which is later than a gate would have told them.
- The hostile-name test fixture was carried across verbatim rather than rewritten, because it covers five escaping classes that a simpler fixture would not, and it is regression cover for a defect that actually shipped.

## Alternatives considered

**Publish the unified template under a new name and leave the layers in.**
Rejected.
It makes the standard's distribution channel an advertisement for one team's stack, and it keeps every adopter reading past twelve irrelevant questions to reach the six that matter.
The maintenance argument runs the other way too: the toggles are cheap to keep only until the first change that has to be correct in all seven combinations.

**Keep one repository and make governance-only the default render.**
Rejected as cosmetic.
The application and tooling layers would still be present in the tree, still need testing, and still be the first thing a reader sees.

**Git-filter-repo the governance history across, so the split keeps provenance.**
Rejected.
The carried files were also edited during extraction (path flattening, Jinja collapse, the README rewrite), so the transplanted history would describe files that no longer exist at paths that no longer exist.
Provenance is recorded here instead, by naming the source commit.

**Ship the pin-to-tags check anyway, as a standalone script with no preset around it.**
Rejected.
It would be the one piece of tooling in a template that promises none, it needs wiring into a gate the consumer owns, and an unwired check is a file nobody runs.
