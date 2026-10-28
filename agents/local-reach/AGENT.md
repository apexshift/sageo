---
name: local-reach
description: >-
  Diagnose Google Business Profile quality, LocalBusiness schema, and NAP
  consistency when Reach is local. Required Human review before GBP/listing
  change recommendations are finalised. Orchestrator omits this Agent when
  Reach ≠ local.
metadata:
  version: "0.1.0"
  primary_outcome: SEO
  skills: gbp-profile-auditor,local-schema-checker,citation-consistency-checker
  human_review_gate: required
  cost_model: tokens_and_connector_calls
---

## Purpose

Coordinate Local / Geographic Skills into one local Reach audit: GBP profile
quality, LocalBusiness schema, and NAP/citation consistency. Primary outcome
is SEO. This Agent never routes to other Agents; Orchestrator routing decides
when Reach=local applies.

## When to use

- **Reach=local** — Orchestrator includes this Agent when practitioner Reach is
  local (or multi-location local intent). When Reach ≠ local, the Orchestrator
  omits this Agent; routing policy itself is unchanged by this package.
- Practitioner needs GBP → local schema → NAP findings before finalising listing
  change recommendations.

## Inputs

- **run context** — run id and property refs from the Orchestrator / practitioner.
- **reach** — expected `local` when this Agent is scheduled (Orchestrator-owned).
- **gbp_profile** — GBP profile capture for `gbp-profile-auditor`.
- **page_captures** — location/page HTML for `local-schema-checker`.
- **nap_sources** — name/address/phone sources for `citation-consistency-checker`.

## Outputs

- **findings** — GBP, LocalBusiness schema, and NAP consistency findings.
- **evidence_ids** — Evidence ids from invoked Skills for the Decision log.
- **GBP/listing change recommendations (draft)** — not final until Human review
  approval at the required gate.

## Skills invoked

1. `gbp-profile-auditor` — audit Google Business Profile quality first.
2. `local-schema-checker` — validate LocalBusiness (and related) schema.
3. `citation-consistency-checker` — check NAP consistency across sources.

## Evidence

Aggregate Skill Evidence by reference (`evidence_ids` on Decision log entries).
Do not invent metrics when sources fail — keep dependent claims at
`needs_human_verification`.

## Human review points

`human_review_gate: required`. Pause after Skills complete and before any
GBP/listing change recommendations are finalised. The Orchestrator owns the
system stop; this Agent declares the gate. Resume records Human approval or
rejection in the Decision log.

## Cost

`cost_model: tokens_and_connector_calls`.

- **cost_drivers** — fixture-first Skill work; later read-only connectors if
  added for GBP or citations.
- **unit_estimates** — labelled estimates only; exact figures wait for the P5
  metrics helper.

## Procedure / workflow

1. Resolve inputs (GBP profile, page captures, NAP sources) under Reach=local
   scheduling from the Orchestrator.
2. Invoke Skills in declared order: GBP → local schema → NAP. Write a Decision
   log entry with `skills` and `evidence_ids` (`actor: agent`).
3. Pause for required Human review before marking GBP/listing change
   recommendations final. Resume on approval (or stop on rejection).
4. Hand off completion to the Orchestrator. No Agent→Agent routing from this
   package.
