---
name: local-schema-checker
description: >-
  Validate LocalBusiness structured data on a page fixture and emit Evidence for
  each claim. Use when checking local rich-result eligibility fields (name,
  address, telephone) on captured HTML.
metadata:
  version: "0.1.0"
  capability_pillar: local-geographic
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: page-html
  outputs: findings, evidence
---

## Purpose

Validate schema.org **LocalBusiness** structured data on a page (fixture or
captured HTML) for local / rich-result eligibility signals: presence, name,
address (`streetAddress` + `addressLocality`), and telephone. Complements
page-generic `schema-validator`. Findings stay Skill-level; remediations are
owned by Agents and Orchestrator Human review gates.

## Inputs

- **page-html** — HTML document string (or path resolved by the caller) that may
  contain `application/ld+json` script blocks with LocalBusiness.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/check.py` →
`check_local_schema(html, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `local-jsonld-parse`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load the page HTML from the caller (fixture or capture). No live APIs.
2. Collect `script[type="application/ld+json"]` blocks and attempt JSON parse.
   Each unparseable block → fail `local_schema.jsonld.parse` (high confidence).
3. From successfully parsed JSON, select entities whose `@type` is or includes
   `LocalBusiness` (including `@graph` / array roots).
4. If none and not every block failed parse → fail `local_schema.present`.
   If every block failed parse, return parse findings only.
5. Otherwise pass `local_schema.present`, then score the first entity for:
   - **name** — non-empty string
   - **address** — object with non-empty `streetAddress` and `addressLocality`
   - **telephone** — non-empty string
6. If multiple LocalBusiness entities disagree on name, telephone, or
   `streetAddress`, add fail `local_schema.nap_conflict` with
   `confidence: needs_human_verification`.
7. Return `{findings, evidence}`.
