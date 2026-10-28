---
name: sageo-orchestrator
description: >-
  Route and prioritise Agents, sequence multi-agent flows on a shared Run
  directory, and enforce Human review gates. Never calls Skills directly;
  Agents never route to other Agents.
metadata:
  version: "0.1.1"
---

## Purpose

Coordinate which Agent(s) run for a practitioner request, prioritise queued
work, sequence multi-agent flows, and **enforce** Human review gates. The
Orchestrator never invokes Skills; Agents compose Skills. Agents never route
to other Agents — only this Orchestrator owns sequencing.

## Routing

1. Parse the run request for **goal**, **primary_outcome** (`SEO` | `AIO` |
   `GEO`), and optional **Reach** (`local` | `national` | `global`).
2. Select Agents whose When-to-use matches the request **intent** and whose
   `primary_outcome` matches (and Reach when the Agent declares it).
3. Unknown or unmatched intent → Decision log entry with ask-human / NHV
   Evidence; **do not invent** an Agent or fabricate a route.
4. Optional playbook `thin_audit` schedules Agents by pipeline role:
   Technical → Content/AIO → (local-reach when Reach=`local`) → Measurement.
   When Reach is `national`, `global`, or unset, local-reach is omitted.

## Prioritisation

1. When every scheduled Agent carries severity and impact scores (1–5), order
   by **severity × impact** descending (stable by Agent name on ties).
2. Otherwise **FIFO** within the run (registration / schedule order).
3. Human-gated remediations never auto-advance.
4. Cost estimates may annotate the queue; they must **not** skip gates.

## Multi-agent

- Default pattern: **sequential** Agents sharing one **Run directory**
  (`runs/<id>/`).
- Thin audit schedule (when Agents are available):
  1. Technical findings
  2. Content / AIO
  3. Local Reach (only when Reach=`local`)
  4. Measurement / Evidence
- Parallel fan-out only when the Orchestrator explicitly schedules independent
  Agents with no cross-Agent Skill calls; join before any shared
  remediation / gate.
- Evidence and Decision logs append into the shared Run directory.

## Human review

- Agents declare *when* a gate is needed (`human_review_gate` plus Human
  review points).
- The Orchestrator **owns the stop**: no progression past a required gate
  without recorded human approval in the Decision log
  (`human_review: approved`).
- Applies especially before finalising remediations or any live-site-affecting
  plan (live mutation remains out of scope through P5).
- Gates are never skipped to save cost.

## Decision logging

The Orchestrator writes append-only Decision log entries under `runs/<id>/`
for routing, prioritisation, multi-agent schedule, and gate stop/resume.
Required shape: `decision_id`, `actor` (`orchestrator`), `timestamp`,
`inputs`, `skills` / `agents` involved, `outcome`, `evidence_ids`,
`human_review`, `rationale`. No in-place edits; corrections are new entries.

## Inputs/Outputs

**Inputs:** run goal, property/site refs, `primary_outcome`, optional Reach,
optional playbook hint, and the in-process Agent set for this run.

**Outputs:** `run_id`, ordered Agent invocations and statuses, Evidence id
refs, open/closed / awaiting-approval gate state, Decision log pointer under
the Run directory. No auto-publish.
