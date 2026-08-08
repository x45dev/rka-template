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
of the four RKA values are not OKF values. An OKF-conformant consumer reading a document this
template shipped at `status: archived` does not read "retired" - it reads an unrecognized value,
and OKF section 11's permissive rules ("MUST NOT reject", "treat all other constraints as soft
guidance") steer it toward treating the document as live. **A retired document reads as current.**
That is the exact failure the `status` lifecycle exists to prevent, reintroduced at the boundary
between the two standards.

The reconciliation is available and it improves RKA rather than merely repairing it. OKF v0.2
sections 5.2 and 5.3 add `verified` and derive **trust tiers** from it: absent means unverified, a
non-`human:` actor means machine-confirmed, and a `human:<id>` actor means human-reviewed. That
top tier is precisely this repository's central invariant - "nothing becomes `canonical` without a
human deciding it" - which today is prose that the shipped `AGENTS.md` openly says no gate
enforces.

RKA's four-value `status` is therefore two axes sharing one key. `draft` and `archived` are
publication lifecycle, which is OKF `status`. The `active`-versus-`canonical` distinction is
warrant, which is OKF `verified`. They were merged because RKA had only one field to put them in.

## Decision

**RKA is a profile of OKF v0.2: a strict superset that narrows OKF's reserved keys and extends it
with what OKF's non-goals deliberately exclude. This repository distributes that profile.**

1. **An RKA bundle is an OKF bundle.** Every document this template ships satisfies OKF section 11
   conformance, and the shipped validator gains a check that says so rather than leaving it to
   inspection.

2. **The profile adds only what OKF declines to specify:** document identity (`id` and the
   id/filename conventions), `version`, the ADR shape (`adr_status`), the governed spec-bundle
   lifecycle, the mandatory constitution, bundle-index integrity, and the extraction-record rule.
   OKF's non-goals name most of these as out of scope for the format, so the profile is additive
   by construction rather than by negotiation.

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

5. **`date` is superseded by `generated: { by, at }`**, taking OKF v0.2's own breaking change from
   v0.1 (section 13.1) rather than maintaining a parallel field.

6. **The promotion invariant becomes enforceable and is enforced.** The validator requires a
   `verified` entry's `by` to carry the `human:` prefix before a document counts as canonical, and
   rejects any `by` that is not one of OKF section 7's three actor forms. The prose rule about
   intent stays; the artifact it produces stops being unverifiable.

7. **The repository keeps its name and its scope.** It distributes the profile, and nothing else -
   no task runner, no lint preset, no CI. That invariant is untouched.

## Consequences

* **The "governance layer and nothing else" invariant gets sharper, not looser.** What this
  template ships is now nameable in one line: OKF v0.2 plus the RKA profile. A consumer can adopt
  the baseline from the specification and take this template for the profile.
* **Every shipped seed document and this repository's own `knowledge/` migrate.** A breaking
  schema change, travelling as a release train with numbered manual steps, never as a silent
  update.
* **The archived-reads-as-live defect closes**, because after migration there is one vocabulary.
* **The single most important RKA rule stops being unenforceable.**
* **The template acquires an upstream it does not control.** OKF is external and has already made
  two breaking changes in one minor bump. Tracking it is now a standing obligation, and the
  bundle-root `index.md` `okf_version` declaration is what keeps a bundle's target honest.
* **`workspace-template` and this repository become distinguishable by product.** That one
  distributes a workspace with the profile as a toggle; this one distributes the profile. Their
  `ADR-0017` is the matching record.

## Alternatives considered

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
