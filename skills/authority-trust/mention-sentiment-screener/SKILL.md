---
name: mention-sentiment-screener
description: >-
  Screen brand mentions from an opportunity-corpus fixture for sentiment and
  reputation risk, emitting Evidence. Use when assessing mention risk; never for
  suppression campaigns or paid reputation manipulation.
metadata:
  version: "0.1.0"
  capability_pillar: authority-trust
  primary_outcome: SEO
  secondary_outcomes: AIO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: opportunity-corpus
  outputs: findings, evidence
---

## Purpose

Screen **brand mentions** in a hermetic opportunity corpus for sentiment and
reputation risk. Candidates must mention the brand; clear positive/neutral
mentions with empty risk signals pass, negative or risk-flagged mentions fail,
and mixed or contradictory cues emit `needs_human_verification`. Findings stay
Skill-level; outreach, suppression, or live-site changes are owned by Agents and
Orchestrator Human review gates.

## Inputs

- **corpus** — map with `brand` (string) and `candidates` (list of candidate
  maps). Each candidate may include `id`, `title`, `url`, `snippet`,
  `mentions_brand`, `sentiment` (`positive` | `neutral` | `negative` | `mixed`),
  `risk_signals`.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/screen.py` →
`screen_mention_sentiment(corpus, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `mention-sentiment-heuristics`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
outreach, suppression campaign, or live-site change requires Agent/Orchestrator
gates.

## Procedure

1. Load the opportunity corpus from the caller (fixture or capture). No live APIs.
2. For each candidate that `mentions_brand`, classify:
   - **clear** — `sentiment` in `positive` | `neutral` and empty `risk_signals`
   - **conflict** — `sentiment` is `mixed`, or safe sentiment cues plus risk cues
     → NHV
   - **risk** — `sentiment` is `negative` or non-empty `risk_signals` without a
     safe+risk conflict
   - **rejected** — otherwise (no brand mention to screen)
3. If any clear → pass `mention.sentiment_ok` + `mention.low_risk` with
   per-candidate Evidence; else fail `mention.sentiment_ok`.
4. If any risks → fail `mention.risk_detected` with high-confidence Evidence.
5. If any conflicts → fail `mention.signal_conflict` with
   `needs_human_verification` Evidence.
6. Return `{findings, evidence}`. Never propose suppression or paid reputation
   manipulation.
