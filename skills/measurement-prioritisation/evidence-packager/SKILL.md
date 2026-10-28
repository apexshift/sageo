---
name: evidence-packager
description: >-
  Package an evidence-bundle of upstream findings and Evidence into a
  review-ready bundle for Human review gates. Use when assembling Measurement
  outputs without inventing new claims (evidence_requirement: partial).
metadata:
  version: "0.1.0"
  capability_pillar: measurement-prioritisation
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  evidence_requirement: partial
  human_review_gate: not_required
  inputs: evidence-bundle
  outputs: package, findings, evidence
---

## Purpose

Package upstream **findings** and **Evidence** into a review-ready bundle for
Human decision. This Skill is `evidence_requirement: partial`: procedural
bundling steps may be claim-free, but any factual claim about the bundle still
gets Evidence. It does not invent SEO/AIO/GEO metrics. Remediations and live
changes remain Agent/Orchestrator Human review gates.

## Inputs

- **evidence-bundle** — map with `findings` (list of `{id, status, summary}`),
  `evidence` (list of Evidence maps), and optional `ranked_ids` (list of finding
  id strings from a prior prioritiser).
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **package** — review-ready bundle map: `ready_for_review`, counts
  (`finding_count`, `evidence_count`, `nhv_count`), `ranked_ids`, and the
  passed-through `findings` / `evidence` lists.
- **findings** — list of `{id, status, summary}` records (`pass` | `fail`) about
  packaging quality.
- **evidence** — Evidence records only for packaging claims (partial).

Executable entry: `scripts/package.py` →
`package_evidence(evidence_bundle, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: partial` — procedural assembly of the package object does
not require Evidence. Any claim this Skill emits (counts, incompleteness,
ranked_ids preservation, NHV pending) is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `evidence-bundle-package`)

## Human review

`human_review_gate: not_required`. This Skill packages for review; it does not
approve remediations. Agents/Orchestrator own the stop before live change or
final remediation approval.

## Procedure

1. Load the evidence-bundle from the caller. No live APIs. Do not invent claims
   about the underlying site or rankings.
2. Require `findings` and `evidence` to be lists (missing keys → empty lists).
   Optional `ranked_ids` must be a list of strings when present.
3. Validate each Evidence record for required fields (`claim`, `source`,
   `observed_at`, `confidence`). When `confidence` is
   `needs_human_verification`, also require `verification_reason`.
4. Count NHV Evidence records. Build `package` with counts, ranked_ids
   (default `[]`), and passthrough findings/evidence.
5. If both findings and evidence lists are empty → fail `package.ready`
   (`ready_for_review: false`).
6. Else if any Evidence record is incomplete → fail `package.ready` and
   `package.incomplete` (`ready_for_review: false`).
7. Else pass `package.ready` (`ready_for_review: true`). If `nhv_count` > 0,
   also fail `package.nhv_pending` (surfaces items needing human verification;
   counting NHV is high-confidence observation).
8. Emit Evidence only for the packaging claims above. Return
   `{package, findings, evidence}`.
