---
name: schema-validator
description: >-
  Validate schema/structured data on a page fixture and emit Evidence for each
  claim. Use when checking JSON-LD or other structured data on a captured page.
metadata:
  version: "0.1.0"
  capability_pillar: technical-foundation
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: page-html
  outputs: findings, evidence
---

## Purpose

Validate schema.org / structured data on a page (fixture or captured HTML) and
emit Evidence for every claim. Findings stay Skill-level; remediations are owned
by Agents and Orchestrator Human review gates.

## Inputs

- **page-html** — HTML document string (or path resolved by the caller) that may
  contain `application/ld+json` script blocks.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/validate.py` → `validate_page(html, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `jsonld-parse`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load the page HTML from the caller (fixture or capture).
2. Collect `script[type="application/ld+json"]` blocks.
3. For each block, attempt JSON parse:
   - Valid JSON with `@type` → pass finding + high-confidence Evidence.
   - Valid JSON missing `@type` → fail finding + medium-confidence Evidence.
   - Present but not valid JSON → fail finding + high-confidence Evidence
     (parse failure is machine-decidable).
   - No JSON-LD blocks → fail finding + high-confidence Evidence that none were
     observed.
4. If multiple Organization blocks disagree on `name`, add a fail finding and
   Evidence with `confidence: needs_human_verification` (contradictory sources).
5. Return `{findings, evidence}` without calling live APIs.
