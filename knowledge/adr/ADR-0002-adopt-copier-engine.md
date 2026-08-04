---
id: ADR-0002
title: Adopt Copier as the templating engine
status: canonical
version: 0.1.0
date: 2026-07-31
adr_status: accepted
type: adr
---

# ADR-0002 - Adopt Copier as the templating engine

## Context

This decision is carried forward from the predecessor unified template, where it was recorded as its ADR-0005 and where the alternative under consideration was cookiecutter.
The reasoning is still load-bearing here, so it is restated rather than referenced across a repository boundary.

The objective RKA is built for - apply the governance layer to *new and existing* projects, and let an *evolving* standard propagate to projects that already adopted it - is one cookiecutter structurally cannot serve.
cookiecutter is greenfield-only: it generates a new directory once, has no first-class way to render into an existing repository, and offers no update path when the template changes.

That gap was identified before the predecessor was built.
The reference adopter project (a private sibling repo) had already recommended Copier for exactly this reason, finding that updatability was the deciding factor, and the recommendation was silently dropped when the templates were first built as cookiecutter.

[Copier](https://copier.readthedocs.io/) supports both missing capabilities natively.
`copier copy` can target an existing directory, and `copier update` re-applies template evolution to already-generated projects via a three-way merge against a committed `.copier-answers.yml`.

## Decision

Use Copier as the templating engine.

1. **Render root is `template/`**, declared via `_subdirectory: template`, so the repository's own `README.md`, `AGENTS.md`, `knowledge/` and `tests/` are never generated into a consumer.
2. **`_templates_suffix: ""`**, so every file under `template/` is templated in place and bare `{{ var }}` renders without a `.jinja` extension on every file.
3. **Conditional inclusion is path-based.**
   A file whose path segment renders empty is not emitted, which is how the `LICENSE` question works without any post-generation hook.
4. **No generation hooks.**
   Generation shells out to nothing, so a bare Python and Copier machine succeeds and no `--trust` prompt is needed for a hook.
5. **Ship `template/{{ _copier_conf.answers_file }}`**, so every generated repository carries a committed `.copier-answers.yml` - the file `copier update` reads.

## Consequences

- A generated repository can pull later template changes with `copier update`, so the standard can evolve and reach every adopter.
- The layer can be applied to an *existing* repository (`copier copy gh:... .`), which is the brownfield adoption path RKA needs and which cookiecutter could not provide.
- `_templates_suffix: ""` has a sharp edge that outlives this decision: every shipped file is Jinja, so a shipped shell script containing `{` immediately followed by `#` is silently mangled at render time.
  ADR-0001 records the mitigation, and the generation suite greps the template source for it.
- Copier's `_skip_if_exists` is available but deliberately unused.
  On copier 9.17.0 it is write-once: a file listed there is never updated again once it exists in the destination, which would permanently freeze the shipped guidance in every existing project.
  Consumer-owned files are reconciled by three-way merge and release notes instead.

## Alternatives considered

**cookiecutter.**
Rejected: it fails the new-and-existing-projects objective outright, and it has no update path for an evolving standard.

**cookiecutter plus cruft**, bolting update-tracking onto cookiecutter.
Rejected as a destination.
It is a weaker three-way update than Copier's and an extra dependency, and it would only ever have been a bridge.

**A plain repository that adopters copy files out of by hand.**
Rejected.
It is the brownfield path and nothing else: no answers file, no update mechanism, and no way to tell an adopter which version of the standard they are on.
