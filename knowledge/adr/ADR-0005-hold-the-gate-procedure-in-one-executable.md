---
id: ADR-0005
title: Hold the gate procedure in one executable
status: draft
version: 0.1.0
date: 2026-08-03
type: adr
adr_status: accepted
---

# ADR-0005: Hold the gate procedure in one executable

## Context

Two Copier behaviours make a gate examine code nobody just wrote, and both pass while doing it.

1. The default `--vcs-ref` for a git template is its latest **tag**.
   This repository is tagged, so a bare `copier copy --defaults --trust . /tmp/rka-render` renders the last release, and every gate chained off that render reports on it.
2. Copier reads an existing destination as an update.
   It conflicts on the first changed file and, in a non-interactive run, exits non-zero having written nothing.
   The destination still holds the previous render, and the validator and BATS steps that follow are separate commands with no way to know.

Both were live defects, found this session and fixed in the documents.
The mechanism that held them fixed is what this record is about.

The render command was written out at six sites: twice in `AGENTS.md`, twice in `README.md`, and twice in `.github/workflows/ci.yml`.
`tests/test_gate_invocations.py` parsed those commands back out of the surrounding markdown and asserted the two properties over each copy.

Three rounds of adversarial review were run against that guard.
They found twelve defects **in the parser** and none in the documents:
a clean counted wherever it appeared rather than before the render;
`/tmp` itself, `/var/tmp` and `//tmp/...` fell outside the check by spelling;
a commented-out `rm -rf` counted as a clean;
`rm -rf /tmp/other/tmp/dst` counted as a clean of `/tmp/dst`;
an unbalanced fence elsewhere in a document mis-scoped every later block;
and running prose containing the words "copier copy ." parsed as a command, which this repository's documents make likely because they discuss that exact trap at length.

The rate of discovery was not falling.
Two properties explain why, and they are properties of the approach rather than of any particular bug.
The input domain is arbitrary markdown, which has no edge.
And the failure mode is silent: a hole in a guard over prose is indistinguishable from a document with no defect, so the guard keeps passing either way.

## Decision

Hold the gate procedure in `dev/gates.sh`, and have CI call that script rather than restate its commands.

`AGENTS.md` and `README.md` point at the script instead of carrying copies.
The gate table in `AGENTS.md` keeps a row per gate, naming what each one checks, but no longer carries runnable commands.

`tests/test_gate_invocations.py` drops from 403 lines to roughly a hundred, and stops being a parser.
What it now asserts is the arrangement rather than the copies: that the script exists and is executable, that no prose document restates a render into a scratch destination, that every workflow calls the script rather than rendering directly, that the script's own render pins a ref or goes through the plain-copy directory and clears its destination first, and that a gate which could not run is tracked rather than counted as passing.

The load-bearing property is that **CI calls the script**.
Because CI executes it, a wrong command fails loudly and immediately.
That is the enforcement the parser was standing in for, and it needs no parsing because it is execution.

## Alternatives considered

1. **Keep the guard and close the two remaining holes.**
   Rejected on the rate of discovery rather than on the holes themselves.
   Twelve defects across three cycles, with the third still finding them, is evidence about the approach: parsing prose to validate shell commands has no natural completion point, and each hole is silent until someone happens to look.
2. **Delete the guard and rely on CI alone.**
   Rejected because it reintroduces the failure that started this work.
   CI executes its own commands and so is self-checking, but `AGENTS.md` is the entry point every future session reads, and nothing executes what it says.
   A wrong command there misleads the next agent exactly as it misled this one.
3. **Extract the commands from the documents and have CI run what it extracted.**
   Rejected because it still requires parsing prose, and so inherits the whole defect class rather than escaping it.
4. **Put the script at `scripts/gates.sh`.**
   Rejected on the source-versus-instance rule that `AGENTS.md` section 1 exists to enforce.
   `template/scripts/` is shipped content and a root `scripts/` would sit one path segment away from it, inviting exactly the confusion that section warns about.
   `dev/` cannot be mistaken for shipped content.

## Consequences

- The commands have one definition, so the copies cannot disagree, because there are none.
- A developer or agent runs `bash dev/gates.sh` and gets the same procedure CI runs, including the two traps, without having to know about either.
- This repository now carries a script of its own.
  ADR-0001 point 4 dropped the predecessor's pin-to-tags gate on the grounds that **shipping** a tooling preset is what this template must not do; that reasoning is about `template/`, and this script is not under it.
  The repository already carries `tests/`, `.github/` and `pyproject.toml` on the same footing.
- A gate that cannot run is now reported by the tool rather than by whoever remembers to mention it.
  `bats` is the live case: it is absent from the authoring machine and is not a pip package, so the script names it as not run, and `--strict` makes that fatal in CI, where it is installed.
- Running a single gate now means passing its name rather than copying a line, which is a small loss of directness against the duplication it removes.
- The `--ref` option keeps the committed-ref render available, so the tag trap stays closed for anyone verifying a specific commit.

## Evidence

Run on 2026-08-03, before the documents were changed:

- rendering, editing `template/scripts/validate-frontmatter.sh`, then re-running the documented working-tree command verbatim produced `conflict scripts/validate-frontmatter.sh`, exit 1, and the edit absent from the render;
- the same sequence against `dev/gates.sh` propagates the edit and exits 0;
- the replacement test file was checked to fail when the script is absent, when a workflow renders directly, and when a prose document restates a render.

The twelve parser defects are recorded in the commit messages of `6a7fe43` and `9d91a31`, each reproduced against the live functions before being accepted.
