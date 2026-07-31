---
id: progress
title: Progress
status: active
version: 0.1.0
date: 2026-07-31
type: context
---

# Progress

The state of completion for the template repository.

## What works

- A default `copier copy` renders exactly the governance layer: the seed `knowledge/` tree, `scripts/validate-frontmatter.sh`, `tests/validate-frontmatter.bats`, `AGENTS.md`, `README.md`, `.gitignore`, `.copier-answers.yml`, and `LICENSE` on the MIT arm.
- The generation suite passes, covering render shape, unrendered Jinja, the Jinja comment-open trap in shipped scripts, YAML and JSON parsing, the empty-slug validator, the absence of frontmatter on `AGENTS.md`, the license arms, and a punctuation-hostile project name end to end.
- The rendered validator accepts the rendered seed `knowledge/`, and the shipped BATS suite passes against the render.
- This repository's own `knowledge/` passes the shipped validator, run from a render.
- CI carries the three jobs that reproduce all of the above without a task runner.

## What's left

- A remote, a first release tag, and the published repository name.
- A consumer-facing migration note for projects moving off the predecessor unified template.
- Coverage of the Python yq flavour in the validator probe; only one flavour has been exercised so far.

## Known issues / limitations

- The pin-to-tags update rule is advice in the README, not a gate.
  The predecessor enforced it with a generated check that lived in its tooling preset, and that preset is deliberately not part of this template.
- There is no `copier update` path from the predecessor unified template.
  A project generated from it adopts this template copy-fresh, with a manual reconcile.
- `README.md`, `AGENTS.md`, and `.gitignore` are consumer-owned after the first copy, so a later template change to any of them surfaces as a three-way merge conflict.
