---
id: context
title: Context
status: canonical
version: 0.2.1
date: 2026-08-09
type: context
---

# Context

The combined product, system-pattern, and technical context for the template repository itself.

## Product context

The template serves a repository that wants RKA governance and already has its own toolchain.
One `copier copy` adds `knowledge/` with its seed documents, an `AGENTS.md` entry point, a frontmatter validator, and the validator's BATS suite.
Nothing else arrives, so running it at the root of an existing repository is safe against that repository's own configuration.

The second audience is a greenfield project that wants the governance layer without committing to any particular tooling.
Both get the same render; the template has no toggles.

The third audience is a project that already speaks OKF and wants more than the baseline gives it.
OKF specifies the container and one required field; it deliberately excludes identity, versioning, ADR conventions, spec-bundle lifecycle, and any notion of review or promotion.
This template supplies exactly that gap as a profile (ADR-0006), so adopting it is additive to an existing OKF bundle rather than a migration away from one.

## System patterns

- **Conditional paths, used sparingly.**
  Copier drops a file whose path segment renders empty.
  Only `LICENSE` uses this, gated on the `license` answer.
  Every other path under `template/` is a plain directory, because a conditional path whose condition no longer exists renders empty and the file silently disappears.
- **The render shape is asserted as an exact file set.**
  A positive `is_file()` check cannot notice an *extra* file arriving, which is the failure that would break the "governance layer and nothing else" invariant.
- **The template source is grepped, not just the render.**
  Jinja's comment construct is consumed at render time, so a test that inspects output passes over code that was silently deleted.
  The check reads `template/` directly and selects scripts by shebang rather than by path.
- **The agent entry point sits outside the governed tree.**
  `AGENTS.md` is at the repository root and carries no frontmatter; the generation suite asserts its absence so a later move under `knowledge/` fails here rather than in a consumer's gate.
- **Self-governance runs the shipped artifact.**
  CI renders the template and runs the rendered validator against this repository's own `knowledge/`, so a shipped schema change and this repository's own migration have to land together.

## Technical context

- **The standard layers over OKF, and is defined upstream.**
  RKA's `knowledge/` is a conformant OKF bundle (`repository-knowledge-architecture` ADR-0011); the schema itself is normative in the reference repository, not here.
  The baseline is external and versioned, and has already made two breaking changes between v0.1 and v0.2 (`timestamp` becoming `generated.at`, and the body `# Citations` list becoming frontmatter `sources`), so tracking it is a standing obligation rather than a one-off adoption.
  A bundle declares which revision it targets with `okf_version` in a bundle-root `index.md`, the only place OKF permits frontmatter in an index.
- **Copier 9.x** is the engine, with `_subdirectory: template` and `_templates_suffix: ""`.
- **The shipped validator** is bash, awk, yq and jq only.
  It probes yq by capability (`yq -o=json` first, then bare `yq`) so either the Go or the Python flavour works.
- **The generation suite** is pytest, rendering from a plain (non-git) copy of the working tree so uncommitted edits are validated without a commit-then-test round trip.
- **The shipped test suite** is BATS, which is not a pip package; adopters install it from apt, npm, or a `bats-core` clone.
- **CI** is three GitHub Actions jobs with no task runner of their own: the generation suite, a render followed by the shipped gates, and self-governance plus an em-dash grep.
