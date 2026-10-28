---
name: measurement-evidence
description: >-
  Prioritise issues by severity × impact and package Evidence for Human
  decision. Optional mention-sentiment screen when a corpus is present.
  Required system package gate before the prioritised Evidence pack is approved.
metadata:
  version: "0.1.0"
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  skills: mention-sentiment-screener,severity-impact-scorer,evidence-packager
  human_review_gate: required
  cost_model: tokens_only
---

## Purpose

Coordinate Measurement & Prioritisation Skills (and optional Authority mention
screening) into one cross-cutting workflow that scores issues and packages
Evidence for Human approval. Primary outcome is SEO; secondary AIO and GEO
apply as packaged Evidence may span outcome pillars. This Agent never routes
to other Agents.

## When to use

- Orchestrator schedules the measurement/Evidence step (typically last in the
  default audit sequence after technical and content Agents).
- Practitioner needs severity × impact ranking and a review-ready Evidence pack
  before approving remediation priority.
- Mention risk screening is needed when a mention corpus is available.

## Inputs

- **run context** — run id and property refs from the Orchestrator / practitioner.
- **issue_list** — issues/findings from prior Agents or Skills for severity ×
  impact scoring.
- **corpus** — optional mention corpus for `mention-sentiment-screener`. When
  absent, skip that Skill.
- Prior-run Evidence ids may be referenced; do not invent claims.

## Outputs

- **prioritised findings** — severity × impact ranked issues.
- **evidence package** — review-ready pack from `evidence-packager` (always last).
- **evidence_ids** — Evidence ids for the Decision log.
- The prioritised Evidence / remediation priority pack is **not final** until
  Human approval at the required system package gate.

## Skills invoked

1. `mention-sentiment-screener` — screen mention sentiment **when `corpus` is
   present**; skip when absent.
2. `severity-impact-scorer` — always score severity × impact on the issue list.
3. `evidence-packager` — **always last**; package Evidence for Human review.

## Evidence

Aggregate Skill Evidence by reference (`evidence_ids` on Decision log entries).
Do not invent metrics when sources fail — keep dependent claims at
`needs_human_verification`. Packaging must not invent claims beyond Skill
Evidence.

## Human review points

`human_review_gate: required`. System package gate: pause after Skills complete
and before the prioritised Evidence / remediation priority pack is approved.
The Orchestrator owns the hard stop; this Agent declares the gate. Resume
records Human approval or rejection in the Decision log.

## Cost

`cost_model: tokens_only`.

- **cost_drivers** — tokens on packaged Evidence and scoring; connector-light
  when consuming prior run artifacts.
- **unit_estimates** — labelled estimates only; exact figures wait for the P5
  metrics helper.

## Procedure / workflow

1. Resolve inputs (`issue_list`, optional `corpus`, prior Evidence refs).
2. Select Skills via `scripts/select_skills.py` (skip
   `mention-sentiment-screener` when `corpus` is absent), then invoke screener
   (if selected) → severity-impact-scorer → evidence-packager last. Write a
   Decision log entry with `skills` and `evidence_ids` (`actor: agent`).
3. Pause for the required system package gate before marking the prioritised
   Evidence pack final. Resume on approval (or stop on rejection).
4. Hand off completion to the Orchestrator. No Agent→Agent routing from this
   package.
