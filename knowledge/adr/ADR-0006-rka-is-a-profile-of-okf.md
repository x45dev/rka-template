---
id: ADR-0006
title: RKA is a profile of OKF v0.2
status: draft
version: 0.1.0
date: 2026-08-08
adr_status: proposed
type: adr
---

# ADR-0006 - RKA is a profile of OKF v0.2

## Context

This repository distributes Repository Knowledge Architecture and calls it a standard. Until June
2026 that was accurate in the strong sense: nothing else specified the thing RKA specifies, so RKA
was the whole of its own stack.

Google Cloud then published the **Open Knowledge Format** - v0.1 on 2026-06-12, v0.2 currently -
which specifies knowledge as a directory of markdown files with YAML frontmatter, `type` as its
one required field, `index.md` and `log.md` reserved for bundle structure, standard markdown links
between concepts, and a deliberately permissive conformance rule. That is the shape RKA arrived at
independently, and the shipped validator has cited it since: its header calls `type` "OKF's one
required field" and excludes `index.md` and `log.md` as "reserved OKF bundle-structure files".

So the repository already consumes OKF informally while presenting RKA as freestanding. Two
consequences follow, and the second is a defect.

**RKA has never been justified against the buy-before-build principle.** The ecosystem operating
model puts that principle first and requires a written reason for anything bespoke. RKA has no
such reason on file, because when it was written there was nothing to prefer over it.

**RKA and OKF v0.2 contradict each other on a reserved key.** Both specify `status`. OKF's
vocabulary is `draft | stable | deprecated` with "absent implies `stable`"; RKA's is
`draft | active | canonical | archived`, hard-coded in this repository's `LEGAL_STATUSES`. Three
of the four RKA values are not OKF values.

**The first draft of this record said that made a retired document read as current to an
OKF-conformant consumer. An adversarial review (2026-08-08) checked it against the specification
text and it does not hold.** Section 5.4 defaults only an *absent* `status` to `stable`. Section
11's MUST-NOT-reject list is five items - missing optional fields, unknown `type` values, unknown
additional *keys*, broken cross-links, missing `index.md` - and unknown *values* of a known key are
not among them. Section 11 governs refusing to parse a bundle, not how to interpret a field, so a
consumer that reads `status: archived` and treats it as unknown rather than stable is fully
conformant.

What is real is narrower: **`archived` has no defined meaning to an OKF consumer**, so behaviour is
undefined rather than wrong. That is an interoperability gap worth closing, and the proportionate
close is to rename the value - which is now recorded as the first alternative below, and which the
first draft failed to consider at all.

OKF v0.2 sections 5.2 and 5.3 add `verified` and derive **trust tiers** from it: absent means
unverified, a non-`human:` actor means machine-confirmed, and a `human:<id>` actor means
human-reviewed. That top tier resembles this repository's central invariant - "nothing becomes
`canonical` without a human deciding it" - which today is prose that the shipped `AGENTS.md` openly
says no gate enforces. The first draft treated that resemblance as an opportunity to make the rule
enforceable. It is not: a validator can check that a string begins with `human:`, and cannot check
that a human wrote it.

RKA's four-value `status` is therefore two axes sharing one key. `draft` and `archived` are
publication lifecycle, which is OKF `status`. The `active`-versus-`canonical` distinction is
warrant, which is OKF `verified`. They were merged because RKA had only one field to put them in.

## Decision

**RKA is a profile of OKF v0.2: a strict superset that narrows OKF's reserved keys and extends it
with what OKF's non-goals deliberately exclude. This repository distributes that profile.**

1. **An RKA bundle is an OKF bundle.** Every document this template ships satisfies OKF section 11
   conformance, and the shipped validator gains a check that says so rather than leaving it to
   inspection.

2. **The profile adds identity (`id` and the id/filename conventions), `version`, the ADR shape
   (`adr_status`), the governed spec-bundle lifecycle, the mandatory constitution, bundle-index
   integrity, and the extraction-record rule.** The first draft called all of these "what OKF
   declines to specify". That is false for two of them: OKF section 6.1 says consumers MUST
   tolerate broken links, and section 11 says consumers MUST NOT reject a bundle for broken
   cross-links or a missing `index.md`. RKA's bundle-index rules are still defensible - section 11
   binds *consumers*, and a producer may hold its own bundles to a higher bar than it demands of
   readers - but they are a producer-side house gate that goes beyond the baseline, not a gap the
   baseline left open, and the distinction has to be drawn rather than glossed.

3. **`status` narrows to OKF's vocabulary.** Legal values become `draft`, `stable`, `deprecated`.
   The mapping from the v1 vocabulary is fixed:

   | RKA v1 | OKF v0.2 `status` | Plus |
   | --- | --- | --- |
   | `draft` | `draft` | - |
   | `active` | `stable` | no `verified` entry |
   | `canonical` | `stable` | a `verified` entry whose `by` is a `human:<id>` actor |
   | `archived` | `deprecated` | an `Extraction record` section |

4. **"Canonical" becomes a derived tier, not a stored value.** It keeps its name as RKA's word for
   OKF's human-reviewed tier. This follows OKF's own position that trust is inferred from signals
   rather than stored as a verdict.

5. **`date` is superseded by `generated: { by, at }`.** This is RKA's own change; the first draft
   misattributed it to OKF section 13.1, which supersedes `timestamp` - a field OKF v0.1 had. OKF
   has never specified `date`. The distinction matters because section 13.1's fallback covers
   `timestamp` only, so an unmigrated RKA document's timestamp is invisible to an OKF consumer
   with no fallback path.

6. ~~**The promotion invariant becomes enforceable and is enforced.**~~ **Withdrawn.** A `human:`
   prefix check constrains the shape of a claim, not its truth: the machine actor is the entity
   writing the file. Enforcement would need an out-of-band signal - a commit signature, a
   CODEOWNERS review, a protected-branch attestation - which this record does not have. Closing
   the actor set to section 7's three forms is also unsafe: section 5.1 routes `author` through
   the same convention and then uses `team:...`, a form section 7 does not list.

7. **The repository keeps its name and its scope.** It distributes the profile, and nothing else -
   no task runner, no lint preset, no CI. That invariant is untouched.

## Consequences

* **The "governance layer and nothing else" invariant gets sharper, not looser.** What this
  template ships is now nameable in one line: OKF v0.2 plus the RKA profile. A consumer can adopt
  the baseline from the specification and take this template for the profile.
* **Every shipped seed document and this repository's own `knowledge/` migrate.** A breaking
  schema change, travelling as a release train with numbered manual steps, never as a silent
  update.
* **The `archived` gap closes on the publication axis and reopens on the trust axis.** After
  migration there is one `status` vocabulary. But `verified` is an append-only event list, so a
  document archived after human review still derives as human-reviewed unless a verification event
  is deleted - which is destroying provenance. "Retired but still canonical" replaces "retired but
  unrecognised", so the defect is relocated, not removed.
* ~~**The single most important RKA rule stops being unenforceable.**~~ **Withdrawn**, see decision
  point 6. It also gets worse before it gets better: this repository holds six documents at
  `status: canonical`, and RKA v1 stored neither promoter identity nor promotion time, so the
  migration would have to mint six `verified: { by: human:... }` attestations for reviews with no
  evidence they happened - which OKF then instructs every consumer to read as the top trust tier.
* **The template acquires an upstream it does not control.** OKF is external and has already made
  two breaking changes in one minor bump, which section 12 reserves for a *major* bump - so the
  baseline broke its own versioning contract at v0.2. Hard-coding the things section 12 names as
  rename candidates (the `status` vocabulary, the actor forms) into a shipped validator is a real
  risk, not merely a maintenance obligation. Note also that the `okf_version` declaration named
  here as the honesty mechanism cannot serve that role in this repository: OKF makes it optional,
  RKA makes `index.md` optional, and this repository has no `knowledge/index.md` at all.
* **`workspace-template` and this repository become distinguishable by product.** That one
  distributes a workspace with the profile as a toggle; this one distributes the profile. Their
  `ADR-0017` is the matching record.

## Alternatives considered

* **Rename `archived` to `deprecated` and change nothing else.** **Not considered in the first
  draft.** Once the motivating gap is stated accurately, it is one enum value with the wrong
  spelling, and one rename closes it: a single validator constant, one migration note, no change to
  `date`, no `verified` semantics, no external upstream. This is now the benchmark any wider
  proposal must beat, and the first draft's failure to weigh it is the clearest evidence that
  record was written from its conclusion backwards.
* **Leave RKA freestanding and treat the OKF references as incidental.** Rejected. It leaves the
  archived-reads-as-live defect open and leaves a bespoke standard unjustified against a published
  one in an ecosystem whose first principle is buy-before-build.
* **Keep RKA's `status` values and document a mapping for consumers to apply.** Rejected. A
  mapping nothing executes is a footnote, and the consumers that matter are OKF tools that will
  never read this repository's documentation.
* **Move the RKA lifecycle to a separate `rka_status` key.** Rejected, and kept on the record as
  the fallback. It resolves the collision cheaply and without touching `status`, but it creates
  two lifecycle fields with no mechanism keeping them consistent, and it declines the alignment
  between RKA's trust distinction and OKF's trust tier.
* **Adopt OKF and retire RKA.** Rejected. OKF's non-goals exclude identity, versioning, ADR
  conventions, spec-bundle lifecycle, and any promotion discipline. Those are what this template
  is for.

## Review record

An adversarial fresh-context review on 2026-08-08 kept this record at `proposed`. The corrections
above are its direct result. The full finding list, including the unresolved problems that block
acceptance - the trust-axis lattice, the forgeability of the `human:` check, the provenance the
migration would have to fabricate, and the ways the shipped validator is not yet an OKF-conformant
producer - is recorded once, in `workspace-template` `ADR-0017` under "Review record", rather than
duplicated here where the two copies would drift.

One finding is this repository's alone and is not in that list. `is_reserved()` in the shipped
validator matches `index.md` and `log.md` by basename at *any* depth and skips them from every
rule, while rule 7 validates only the bundle-root index. A nested `knowledge/adr/index.md` carrying
frontmatter therefore passes this template's validator and violates OKF section 8. Decision point 1
("an RKA bundle is an OKF bundle") is consequently an aspiration, not a property, until that is
fixed.

A second, unrelated fail-open was found in the same sweep and is not fixed: rule 9b reads its
checkbox counts through `$(grep -c ... || true)`, so a grep error yields an empty string, bash
arithmetic reads that as zero, and the loop skips the bundle. The rule that catches a spec shipped
in full and never retired silently does not run. It is the same defect shape as the `dev/gates.sh`
em-dash bug fixed alongside this record, in the artifact this decision proposes to rewrite, and it
wants its own change with its own test rather than a drive-by fix.
