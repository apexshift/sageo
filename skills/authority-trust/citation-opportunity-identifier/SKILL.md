---
name: citation-opportunity-identifier
description: >-
  Identify white-hat citation/mention opportunities from an opportunity-corpus
  fixture and emit Evidence. Use when ranking earned-media candidates; never for
  link buying or outreach spam.
metadata:
  version: "0.1.0"
  capability_pillar: authority-trust
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: opportunity-corpus
  outputs: findings, evidence
---

## Purpose

Identify **white-hat** citation/mention opportunities from a hermetic
opportunity corpus (brand + candidate records). Candidates must show a brand
mention or topical relevance, an http(s) URL, and must not be paid placements or
carry spam signals. Findings stay Skill-level; remediations and outreach are
owned by Agents and Orchestrator Human review gates.

## Inputs

- **corpus** — map with `brand` (string) and `candidates` (list of candidate
  maps). Each candidate may include `id`, `title`, `url`, `snippet`,
  `mentions_brand`, `topical_relevance`, `paid_placement`, `spam_signals`.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/identify.py` →
`identify_citation_opportunities(corpus, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `opportunity-corpus-heuristics`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
outreach, content pitch, or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load the opportunity corpus from the caller (fixture or capture). No live APIs.
2. For each candidate, classify:
   - **opportunity** — (`mentions_brand` or `topical_relevance`) and not
     `paid_placement` and empty `spam_signals` and http(s) `url`
   - **conflict** — opportunity cues plus paid/spam risk cues → NHV
   - **rejected** — otherwise (no white-hat opportunity)
3. If any opportunities → pass `citation.opportunity_found` + `citation.white_hat`
   with per-candidate Evidence; else fail `citation.opportunity_found`.
4. If any conflicts → fail `citation.signal_conflict` with
   `needs_human_verification` Evidence.
5. Return `{findings, evidence}`. Never recommend paid links or spam networks.
