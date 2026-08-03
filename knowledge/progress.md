---
id: progress
title: Progress
status: active
version: 0.1.2
date: 2026-08-03
type: context
---

# Progress

The state of completion for the template repository.

## What works

- A default `copier copy` renders exactly the governance layer: the seed `knowledge/` tree, `scripts/validate-frontmatter.sh`, `tests/validate-frontmatter.bats`, `AGENTS.md`, `README.md`, `.gitignore`, `.copier-answers.yml`, and `LICENSE` on the MIT arm.
- The generation suite passes, covering render shape, unrendered Jinja, the Jinja comment-open trap in shipped scripts, YAML and JSON parsing, the empty-slug validator, the absence of frontmatter on `AGENTS.md`, the license arms, and a punctuation-hostile project name end to end.
- The rendered validator accepts the rendered seed `knowledge/`, and the shipped BATS suite passes against the render.
- This repository's own `knowledge/` passes the shipped validator, run from a render.
- Both yq flavours are covered by CI rather than by hand: the `render-and-validate` job runs the validator and the shipped BATS suite once under mikefarah (Go) yq and once under kislyuk (Python) yq, and asserts before each leg that the capability probe selected the branch that leg exists to exercise.
- The repository is published at `github.com/x45dev/rka-template` with `v0.1.0` tagged on the remote, and CI is green on that commit.
- `README.md` carries the consumer-facing migration guidance in two parts: "Brownfield adoption" for adopting into a repository that already has content, and "Consuming this template" for the copy-fresh rule and the absence of an update path from the predecessor.

- The seed documents are `canonical`.
  The owner promoted the constitution, `context.md`, the PRD and all three ADRs on 2026-08-03, on the evidence that CI was green on `v0.1.0` against the shipped validator and that the three ADRs survived a release unamended.
  The transition carries no `version` or `date` bump on the promoted documents, per RKA RFC-003 section 3: a lifecycle transition alone is not a substantive edit.
  `activeContext.md` and `progress.md` stay `active`, because working state is never authoritative.

## What's left

Nothing planned.

## Known issues / limitations

- The pin-to-tags update rule is advice in the README, not a gate.
  The predecessor enforced it with a generated check that lived in its tooling preset, and that preset is deliberately not part of this template.
- There is no `copier update` path from the predecessor unified template.
  A project generated from it adopts this template copy-fresh, with a manual reconcile.
- `README.md`, `AGENTS.md`, and `.gitignore` are consumer-owned after the first copy, so a later template change to any of them surfaces as a three-way merge conflict.
- CI exercises one bash, awk, jq and bats each - whatever `ubuntu-latest` ships - so the validator's portability claim rests on its dependency list rather than on a matrix. The yq matrix exists because that dependency is the one the validator branches on at runtime; the others it merely calls.
