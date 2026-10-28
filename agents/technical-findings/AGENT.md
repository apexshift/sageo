---
name: technical-findings
description: >-
  Diagnose crawl, indexability, schema, and CWV blockers as one technical
  findings workflow. Use for SEO (and generative eligibility) diagnosis before
  Measurement packages Evidence.
metadata:
  version: "0.1.0"
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  skills: crawl-issue-extractor,indexability-checker,schema-validator,cwv-scorer
  human_review_gate: not_required
  cost_model: tokens_and_connector_calls
---

## Purpose

Coordinate Technical Foundation Skills to surface crawl, indexability, schema,
and Core Web Vitals blockers that prevent SEO performance and generative
eligibility. Findings only — the `measurement-evidence` Agent owns the system
package gate. This Agent never routes to other Agents.

## When to use

- Orchestrator schedules a technical diagnosis step (default thin-audit /
  national or local audit sequence).
- Practitioner needs crawl → indexability → schema → CWV findings in one
  workflow before prioritisation.
- Primary outcome is SEO; secondary AIO/GEO apply only as eligibility context.

## Inputs

- **run context** — run id and property refs from the Orchestrator / practitioner.
- **crawl-log** — crawl capture for `crawl-issue-extractor` (fixture or connector).
- **page captures** — HTML / URL fixtures for indexability and schema Skills.
- **lab_metrics** — optional lab CWV metrics (`lcp_ms`, `cls`, `inp_ms`, …).
  When absent, skip `cwv-scorer`.

## Outputs

- **findings** — aggregated Skill findings (crawl, indexability, schema, CWV).
- **evidence_ids** — Evidence ids from invoked Skills for the Decision log.
- Outputs are findings-only; they do not finalise a remediation brief. Measurement
  owns packaging and the required Human review gate.

## Skills invoked

1. `crawl-issue-extractor` — classify crawl-log issues first.
2. `indexability-checker` — check robots/canonical/indexability signals.
3. `schema-validator` — validate structured data on page captures.
4. `cwv-scorer` — score lab CWV metrics **when `lab_metrics` input is present**;
   skip when lab-metrics are absent.

## Evidence

Aggregate Skill Evidence by reference (`evidence_ids` on Decision log entries).
Do not invent metrics when Connectors fail — keep dependent claims at
`needs_human_verification`. Skill package goldens remain the source of truth
for each Skill’s Evidence shape.

## Human review points

`human_review_gate: not_required`. This Agent emits findings only; Measurement
owns the package gate. Pause only on blocking NHV that the practitioner must
resolve before Skills can continue — not a required remediation-brief gate.

## Cost

`cost_model: tokens_and_connector_calls`.

- **cost_drivers** — crawl/SERP connector calls (when used), page-fixture
  processing, deterministic Skill tokens.
- **unit_estimates** — labelled estimates only; exact figures wait for the P5
  metrics helper.

## Procedure / workflow

1. Resolve inputs (crawl-log, page captures, optional `lab_metrics`).
2. Select Skills via `scripts/select_skills.py` (skip `cwv-scorer` when
   `lab_metrics` is absent), then invoke crawl → indexability → schema → CWV
   in declared order. Write a Decision log entry with `skills` and
   `evidence_ids` (`actor: agent`).
3. Return findings and Evidence ids. Do not mark a remediation plan final.
4. Hand off to Orchestrator sequencing (typically `content-aio` then
   `measurement-evidence`). No Agent→Agent routing from this package.
