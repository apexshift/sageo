---
name: cwv-scorer
description: >-
  Score Core Web Vitals (LCP, INP, CLS) against lab/fixture good thresholds and
  emit Evidence for each claim. Use when scoring captured lab metrics for a URL.
metadata:
  version: "0.1.0"
  capability_pillar: technical-foundation
  primary_outcome: SEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: lab-metrics
  outputs: findings, evidence
---

## Purpose

Score Core Web Vitals from a lab-metrics fixture against clear good thresholds
(LCP ≤ 2500ms, INP ≤ 200ms, CLS ≤ 0.1). Findings stay Skill-level; remediations
are owned by Agents and Orchestrator Human review gates. Evidence is labelled as
lab (not field/CrUX).

## Inputs

- **metrics** — map with numeric `lcp_ms`, `inp_ms`, and `cls` from a lab
  capture (Lighthouse or equivalent fixture).
- **alternate_metrics** — optional second lab capture of the same shape; when
  present and disagreeing on pass/fail for any metric, emit an NHV finding.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/score.py` →
`score_cwv(metrics, *, source, observed_at=None, alternate_metrics=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `lab-metrics-threshold`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load lab metrics from the caller (fixture or capture). No live APIs.
2. Score **LCP** (`lcp_ms`): ≤ 2500 → pass; otherwise fail. Emit Evidence.
3. Score **INP** (`inp_ms`): ≤ 200 → pass; otherwise fail. Emit Evidence.
4. Score **CLS** (`cls`): ≤ 0.1 → pass; otherwise fail. Emit Evidence.
5. If `alternate_metrics` is provided and any metric's pass/fail disagrees with
   the primary capture, add a fail finding and Evidence with
   `confidence: needs_human_verification`.
6. Return `{findings, evidence}`.
