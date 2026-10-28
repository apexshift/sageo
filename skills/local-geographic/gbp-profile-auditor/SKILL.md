---
name: gbp-profile-auditor
description: >-
  Audit Google Business Profile completeness and quality signals from a
  gbp-fixture snapshot and emit Evidence. Use when checking GBP readiness
  for local Reach without live APIs.
metadata:
  version: "0.1.0"
  capability_pillar: local-geographic
  primary_outcome: SEO
  secondary_outcomes: AIO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: gbp-fixture
  outputs: findings, evidence
---

## Purpose

Audit **Google Business Profile (GBP)** completeness and quality signals from a
fixture snapshot: name, address, telephone, website, primary category, hours,
description length, and photo count. Optional alternate snapshots that disagree
on identity fields emit `needs_human_verification`. Findings stay Skill-level;
remediations (including GBP edits) are owned by Agents and Orchestrator Human
review gates.

## Inputs

- **gbp-fixture** — map with profile fields: `name`, `streetAddress`,
  `addressLocality`, `telephone`, `website`, `primaryCategory`, `description`,
  `hours` (day→hours map), `photoCount` (integer). Optional `alternate` map
  with overlapping identity fields for conflict checks.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/audit.py` →
`audit_gbp_profile(profile, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `gbp-fixture-heuristics`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live GBP / listing change requires Agent/Orchestrator
gates.

## Procedure

1. Load the gbp-fixture profile from the caller. No live APIs.
2. Score completeness fields (non-empty string unless noted):
   - **name** → `gbp.name`
   - **address** → `gbp.address` when both `streetAddress` and
     `addressLocality` are non-empty
   - **telephone** → `gbp.telephone`
   - **website** → `gbp.website`
   - **primaryCategory** → `gbp.category`
   - **hours** → `gbp.hours` when the hours map has ≥1 day with a non-empty
     value
3. Score quality fields:
   - **description** → `gbp.description` when length ≥ 50 characters
   - **photoCount** → `gbp.photos` when integer count ≥ 3
4. If `alternate` is present and disagrees with the primary on any of `name`,
   `streetAddress`, `addressLocality`, or `telephone` (text casefold; phone
   digits, dropping a leading country `1` when 11 digits), fail
   `gbp.profile_conflict` with `needs_human_verification` Evidence.
5. Return `{findings, evidence}`.
