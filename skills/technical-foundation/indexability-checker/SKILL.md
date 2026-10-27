---
name: indexability-checker
description: >-
  Assess indexability signals from HTTP status, X-Robots-Tag, and robots meta
  on a headers-html fixture and emit Evidence for each claim. Use when checking
  whether a captured URL is eligible to be indexed.
metadata:
  version: "0.1.0"
  capability_pillar: technical-foundation
  primary_outcome: SEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: headers-html
  outputs: findings, evidence
---

## Purpose

Assess core indexability signals from a captured HTTP response (status +
headers) and HTML body. Findings stay Skill-level; remediations are owned by
Agents and Orchestrator Human review gates.

## Inputs

- **status** — HTTP status code of the captured response.
- **headers** — response header map (case-insensitive names); may include
  `X-Robots-Tag`.
- **html** — HTML document string that may include a robots meta tag.
- **source_response** / **source_html** / **source_bundle** — stable ids for
  Evidence `source` (fixture paths, URL, or doc ids).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/check.py` →
`check_indexability(*, status, headers, html, source_response, source_html, source_bundle, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `headers-html-parse`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load status, headers, and HTML from the caller (fixture or capture).
2. Evaluate **HTTP status**:
   - `200` → pass finding + high-confidence Evidence.
   - otherwise → fail finding + high-confidence Evidence (not eligible as a
     primary indexable URL).
3. Evaluate **X-Robots-Tag** (case-insensitive header name):
   - absent → pass (no blocking directive observed).
   - contains `noindex` or `none` → fail.
   - otherwise → pass (allows indexing).
4. Evaluate **robots meta** (`<meta name="robots" content="…">`):
   - absent → pass.
   - contains `noindex` or `none` → fail.
   - otherwise → pass.
5. If both X-Robots-Tag and robots meta are present and disagree on whether
   indexing is blocked, add a fail finding and Evidence with
   `confidence: needs_human_verification`.
6. Return `{findings, evidence}` without calling live APIs.
