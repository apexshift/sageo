---
name: entity-coverage-checker
description: >-
  Check topical/entity coverage on a page fixture (named schema entity, sameAs
  identity links, visible name mention) and emit Evidence. Use when assessing
  answer-quality entity gaps on captured HTML.
metadata:
  version: "0.1.0"
  capability_pillar: content-answer-quality
  primary_outcome: AIO
  secondary_outcomes: SEO, GEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: page-html
  outputs: findings, evidence
---

## Purpose

Check hermetic **entity coverage** signals on a page (fixture or captured HTML):
a named schema.org entity (`Organization`, `Person`, `Product`, `Brand`,
`Place`, or `LocalBusiness`), `sameAs` identity links, and whether the entity
name appears in visible text. Findings stay Skill-level; remediations are owned
by Agents and Orchestrator Human review gates.

## Inputs

- **page-html** — HTML document string (or path resolved by the caller).
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/check.py` →
`check_entity_coverage(html, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `entity-html-parse`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load the page HTML from the caller (fixture or capture). No live APIs / LLMs.
2. Collect `application/ld+json` blocks; each unparseable block → fail
   `entity.jsonld.parse` (high confidence).
3. Select entities whose `@type` intersects Organization / Person / Product /
   Brand / Place / LocalBusiness and that have a non-empty `name`.
4. If none (and not parse-only failures) → fail `entity.schema_present`.
5. Otherwise pass `entity.schema_present` for the first named entity, then:
   - **sameAs** — pass if one or more identity URLs; else fail
   - **visible mention** — pass if the entity name appears in visible text
     (scripts/styles stripped); else fail
6. If multiple named entities disagree on `name`, fail `entity.name_conflict`
   with `confidence: needs_human_verification`.
7. Return `{findings, evidence}`.
