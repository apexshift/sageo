---
name: content-aio
description: >-
  Assess intent fit, answer extractability, entity coverage, and white-hat
  citation opportunities for answer/generative surfaces. Carries GEO outcome
  work without geography naming. Required Human review before content-remediation
  briefs are final.
metadata:
  version: "0.1.0"
  primary_outcome: AIO
  secondary_outcomes: GEO, SEO
  skills: intent-classifier,answer-extractability-scorer,entity-coverage-checker,citation-opportunity-identifier
  human_review_gate: required
  cost_model: tokens_and_connector_calls
---

## Purpose

Coordinate Content & Answer Quality and Authority & Trust Skills into one
content/AIO workflow for answer-engine and generative surfaces. Primary outcome
is AIO; secondary GEO and SEO apply as generative and classic search context.
White-hat only — no spam or link schemes. This Agent never routes to other
Agents.

## When to use

- Orchestrator schedules the content/AIO step in the default audit sequence
  (after technical findings when present).
- Practitioner needs intent → extractability → entity → citation assessment
  before a content-remediation brief.
- GEO **outcome** work is carried here (not by a geography-named Agent).

## Inputs

- **run context** — run id and property refs from the Orchestrator / practitioner.
- **page / content captures** — HTML or text fixtures for intent, extractability,
  and entity Skills.
- **authority_inputs** — optional corpus / source list for citation opportunities.
  When absent, skip `citation-opportunity-identifier`.

## Outputs

- **findings** — intent, extractability, entity coverage, and (when run)
  white-hat citation opportunities.
- **evidence_ids** — Evidence ids from invoked Skills for the Decision log.
- **content-remediation brief (draft)** — not final until Human review approval
  at the required gate.

## Skills invoked

1. `intent-classifier` — classify content intent first.
2. `answer-extractability-scorer` — score answer-ready extractability.
3. `entity-coverage-checker` — check entity coverage for answer surfaces.
4. `citation-opportunity-identifier` — identify **white-hat** citation
   opportunities **when `authority_inputs` are present**; skip when absent.
   Spam, paid-link schemes, and manipulative tactics are forbidden.

## Evidence

Aggregate Skill Evidence by reference (`evidence_ids` on Decision log entries).
Do not invent metrics when sources fail — keep dependent claims at
`needs_human_verification`. Citation Evidence must remain white-hat only.

## Human review points

`human_review_gate: required`. Pause after Skills complete and before any
content-remediation brief is marked final. The Orchestrator owns the system
stop; this Agent declares the gate. Resume records Human approval or rejection
in the Decision log.

## Cost

`cost_model: tokens_and_connector_calls`.

- **cost_drivers** — LLM-heavy judgment Skills (intent, extractability, entity,
  citation); optional connector samples later.
- **unit_estimates** — labelled estimates only; exact figures wait for the P5
  metrics helper.

## Procedure / workflow

1. Resolve inputs (content captures, optional `authority_inputs`).
2. Select Skills via `scripts/select_skills.py` (skip
   `citation-opportunity-identifier` when `authority_inputs` is absent), then
   invoke intent → extractability → entity → citation in declared order.
   Write a Decision log entry with `skills` and `evidence_ids` (`actor: agent`).
3. Pause for required Human review before marking any content-remediation brief
   final. Resume on approval (or stop on rejection).
4. Hand off to Orchestrator sequencing (typically `measurement-evidence` next).
   No Agent→Agent routing from this package.
