# AGENTS.md

{{ project_name }} follows **Repository Knowledge Architecture (RKA)**: this project's
durable knowledge lives under `knowledge/`, and each document's frontmatter `status`
records who may change it and how far to trust it. The README documents the lifecycle
and what belongs in which document - read it before your first write to `knowledge/`.

Three things the README does not tell you.

**Nothing becomes `canonical` without a human deciding it.** You may author a promotion,
propose it, and furnish the evidence for it; you never record one. No gate enforces this.

**Extract durable knowledge rather than leaving it in the session.** A single decision
becomes an ADR under `knowledge/adr/`; anything else belongs in `knowledge/context.md`.
Working state goes in `knowledge/activeContext.md` and `knowledge/progress.md`, which are
meant to churn.

**Match the documents next to the one you are writing** rather than inventing a house
style. Frontmatter shape, heading depth, and tone are all visible there, and
`scripts/validate-frontmatter.sh` checks the mechanical parts of `knowledge/**/*.md`.
This project ships no toolchain of its own, so that validator and its BATS suite run
manually or in whatever CI this repository already has:
`bash scripts/validate-frontmatter.sh knowledge`.

The RKA standard itself lives at
[github.com/x45dev/repository-knowledge-architecture](https://github.com/x45dev/repository-knowledge-architecture).
