---
name: severity-impact-scorer
description: >-
  Score an issue-list by severity × impact (1–5 each) and emit Evidence for the
  ranked priorities. Use when deciding what to fix first from structured findings.
metadata:
  version: "0.1.0"
  capability_pillar: measurement-prioritisation
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: issue-list
  outputs: findings, evidence
---

## Purpose

Score structured issues by **severity × impact** so practitioners know what to
fix first. Each dimension is an integer 1–5; the product is the priority score.
Findings stay Skill-level; remediations are owned by Agents and Orchestrator
Human review gates. Optional alternate issue lists that disagree on score emit
`needs_human_verification`.

## Inputs

- **issue-list** — map with `issues` (list of maps). Each issue should include
  `id` (string), optional `summary`, and integer `severity` / `impact` in 1–5.
  Optional `alternate_issues` with the same shape for conflict checks.
- **source** — stable id for the observation (fixture path, URL, or doc id).
- **observed_at** — optional ISO-8601 timestamp; defaults to the run clock when
  omitted by the caller.

## Outputs

- **findings** — list of `{id, status, summary}` records (`pass` | `fail`).
- **evidence** — list of Evidence records (see Evidence).

Executable entry: `scripts/score.py` →
`score_severity_impact(issue_list, *, source, observed_at=None)`.

## Evidence

`evidence_requirement: full` — every claim is an Evidence record with:

- `claim`, `source`, `observed_at`, `confidence`
- `verification_reason` when `confidence` is `needs_human_verification`
- optional `method` (this Skill uses `severity-impact-product`)

## Human review

`human_review_gate: not_required`. This Skill reports findings only. Any
remediation plan or live-site change requires Agent/Orchestrator gates.

## Procedure

1. Load the issue-list from the caller. No live APIs.
2. Require `issues` to be a list. If empty → fail `priority.scored` and stop.
3. For each issue map, validate `severity` and `impact` as integers in 1–5
   (booleans rejected). Valid issues get score = severity × impact.
4. If any issue is incomplete/invalid → fail `priority.scored` and
   `priority.incomplete` with high-confidence Evidence; still emit Evidence for
   any valid scores; do not emit `priority.rank`.
5. Otherwise pass `priority.scored`, rank valid issues by score descending
   (stable by `id` on ties), and pass `priority.rank` naming the top issue.
6. If primary scoring fully succeeded and `alternate_issues` is present, score
   matching ids the same way. When a shared id has two different numeric
   scores, fail `priority.score_conflict` with `needs_human_verification`
   Evidence. Skip this step when incompletes already failed scoring.
7. Return `{findings, evidence}`.
