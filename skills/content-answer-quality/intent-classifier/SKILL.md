---
name: intent-classifier
description: >-
  Classify query and page intent (informational, transactional, navigational)
  with hermetic heuristics and emit Evidence for match/mismatch. Use when
  aligning classic SEO and answer-surface intent on a query-page fixture.
metadata:
  version: "0.1.0"
  capability_pillar: content-answer-quality
  primary_outcome: AIO
  secondary_outcomes: SEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: query-page
  outputs: findings, evidence
---

## Purpose

Classify **query** and **page** intent into informational, transactional, or
navigational using hermetic keyword/structure heuristics, then report whether
they match. Findings stay Skill-level; remediations are owned by Agents and
Orchestrator Human review gates. This Skill does not call an LLM.

## Inputs

- **query** — search/query string from the fixture or caller.
- **page-html** — HTML document string for the candidate page.
- **source_query** / **source_page** / **source_bundle** — stable ids for
  Evidence `source` (fixture paths, URL, or doc ids).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/classify.py` →
`classify_intent(query, page_html, *, source_query, source_page, source_bundle, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `query-page-intent-heuristics`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load query + page HTML from the caller (fixture or capture). No live APIs / LLMs.
2. Classify **query** from token cues:
   - informational: how/what/why/guide/tutorial/…
   - transactional: buy/price/deal/order/…
   - navigational: login/official/website/…
3. Classify **page** from title/H1/body cues (how-to/guide; buy/price/Product;
   login/official/home).
4. Emit `intent.query` / `intent.page` pass when exactly one class matches;
   fail when none match; fail + `intent.ambiguous` with
   `needs_human_verification` when multiple classes match.
5. When both sides have a single class, emit `intent.match` pass/fail.
6. Return `{findings, evidence}`.
