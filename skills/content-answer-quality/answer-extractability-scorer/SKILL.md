---
name: answer-extractability-scorer
description: >-
  Score answer-extractability signals on a page fixture (clear H1, short
  answer-first lead, list/Q&A structure) and emit Evidence. Use when assessing
  whether a page is easy for answer/AI surfaces to extract.
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

Score hermetic **answer-extractability** signals on a page (fixture or captured
HTML): a single clear H1, a short answer-first lead paragraph, and extractable
list or Q&A structure. Findings stay Skill-level; remediations are owned by
Agents and Orchestrator Human review gates. This Skill does not call an LLM.

## Inputs

- **page-html** — HTML document string (or path resolved by the caller).
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/score.py` →
`score_extractability(html, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `html-extractability-parse`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load the page HTML from the caller (fixture or capture). No live APIs / LLMs.
2. Collect non-empty **H1** texts:
   - exactly one → pass `extractability.h1`
   - none → fail
   - more than one → fail `extractability.h1` and fail
     `extractability.signal_conflict` with `needs_human_verification`
3. Take the first non-empty **paragraph** as the lead:
   - word count ≤ 40 → pass `extractability.lead`
   - missing or longer → fail
4. Score **structure**: pass if any of
   - `<ul>`/`<ol>` with ≥ 2 `<li>`
   - `<dl>` with ≥ 1 `<dt>`
   - ≥ 2 `<h2>` texts ending in `?`
   otherwise fail `extractability.structure`
5. Return `{findings, evidence}`.
