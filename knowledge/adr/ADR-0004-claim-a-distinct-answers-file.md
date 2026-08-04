---
id: ADR-0004
title: Claim a distinct Copier answers file
status: draft
version: 0.1.0
date: 2026-08-03
type: adr
adr_status: accepted
---

# ADR-0004: Claim a distinct Copier answers file

## Context

Copier records what a project answered in an answers file, and defaults that file to `.copier-answers.yml` for every template.
The name is therefore contested the moment a repository is generated from more than one template.

This template's stated purpose is adoption into a repository that already exists, and `README.md` names a project moving off the predecessor unified template as the case it expects.
Every such project is already Copier-generated, so for the audience this template was extracted to serve, the collision is the normal case rather than an edge.

Two behaviours found while testing adoption into a real predecessor-generated repository decide the shape of the fix:

1. Copier writes the answers file unconditionally.
   Every other colliding path stops a non-interactive run at the first conflict and prompts in an interactive one; the answers file does neither.
   A default-named answers file is therefore replaced with no conflict, no prompt, and exit code 0.
2. `copier update` resolves the answers file before it resolves the template, because the answers file is where `_src_path` comes from.
   It cannot discover a non-default name on its own.

Sharing the default name has no correct resolution.
Accept the write and the repository loses the link to the template that generated it; decline it and `copier update` never works for this one.

## Decision

Set `_answers_file: .copier-answers.rka-template.yml` in `copier.yml`.

The consequence is carried by the adopter: every `copier update` against this template needs `-a .copier-answers.rka-template.yml`.
Omitting it does not fail.
Copier falls back to `.copier-answers.yml`, finds whatever template that file names, and updates *that* template - so the failure mode of the flag being forgotten is a silent update of the wrong template, which is why `README.md` states it in bold rather than in passing.

## Alternatives considered

1. **Keep Copier's default `.copier-answers.yml`.**
   Rejected on behaviour 1: the collision resolves silently against the adopter, and the population most likely to hit it is the one this template was extracted to serve.
   The rename is also cheapest now and dearer every release after: `v0.1.0` shipped the default name, so the cost is already non-zero and only grows.
2. **Leave the default and document the collision.**
   Rejected because the collision is not survivable by documentation: there is no instruction that preserves both links, only a choice between which one to lose.
3. **Protect the answers file with `_skip_if_exists`.**
   Rejected because `_skip_if_exists` is write-once - the constitution already records this - so it would freeze the answers file at its first value and break `copier update` for this template permanently, which is worse than the collision.
4. **Ship a wrapper script that supplies `-a`.**
   Rejected as a tooling concern, on the same reasoning ADR-0001 used to keep the pin-to-tags gate out: this template carries the governance layer and no tooling, and a consumer that wanted a wrapper can write one against a documented filename.

## Consequences

- **This is a breaking change for anyone who adopted `v0.1.0`**, which shipped the default filename.
  The documented update command cannot find their answers and exits 1 with `Cannot update because cannot obtain old template references from '.copier-answers.rka-template.yml'`.
  The migration is a one-time `git mv .copier-answers.yml .copier-answers.rka-template.yml`, whose contents need no edit, and it is documented in `README.md` rather than left to be discovered.
  No consumer is known - the repository has no forks and a code search finds no `_src_path` pointing at it - but "none found" is not "none exists", and the note costs one paragraph.
- Adoption into an already-Copier-generated repository leaves that repository's answers file byte-for-byte intact, and the two coexist.
- Every update against this template carries a flag, and forgetting it updates a different template rather than erroring.
- `tests/test_generation.py::test_adoption_does_not_clobber_an_existing_answers_file` holds the property, by adopting into a directory that already carries a foreign answers file. It is deliberately separate from the render-shape assertion, which renders into an empty directory where no collision can occur.
- The render shape changes, so `knowledge/PRD.md` FR1 and the `EXPECTED_FILES` set move together with it.

## Evidence

Run on 2026-08-03 against a scratch template repository tagged `v0.2.0` and `v0.3.0` and a consumer repository seeded with a foreign `.copier-answers.yml`:

- adoption left the foreign file byte-identical and wrote `.copier-answers.rka-template.yml` beside it;
- `copier update --vcs-ref v0.3.0` without `-a` resolved `_src_path` from the foreign file and attempted to clone that other template;
- `copier update -a .copier-answers.rka-template.yml --vcs-ref v0.3.0` applied the template change and advanced `_commit` to `v0.3.0`;
- with `_answers_file` removed, the regression test fails: the foreign file is overwritten and the run still exits 0.

A consumer generated from the published `v0.1.0` was then built and used to check the migration: the documented update command exits 1 with a readable message rather than a traceback, and after `git mv` to the new filename the same command exits 0 with `_src_path` and `_commit` unchanged.
