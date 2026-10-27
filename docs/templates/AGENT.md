---
name: example-agent
description: >-
  Workflow this Agent runs and when to use it. Keep under a few lines;
  detail belongs in Purpose, When to use, and Procedure / workflow.
metadata:
  version: "0.1.0"
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  skills: skill-a,skill-b
  human_review_gate: required
  cost_model: tokens_and_connector_calls
---

<!--
  Copy to agents/<agent-name>/AGENT.md
  - name MUST equal the directory name
  - Do NOT set capability_pillar — Agents span pillars via skills
  - primary_outcome ∈ SEO | AIO | GEO
  - skills: comma-separated Skill names (order refined in Skills invoked)
  - human_review_gate ∈ required | not_required
  - cost_model ∈ tokens_and_connector_calls | tokens_only | manual_estimate
  Optional metadata: secondary_outcomes
  Optional body: Failure modes, Examples, Reach
  Agents write Decision log entries; remediations that could affect a live site
  require human_review_gate: required. Agents never route to other Agents.
-->

## Purpose

What workflow this Agent coordinates and which Outcome pillar it primarily serves.

## When to use

Situations and triggers for choosing this Agent (Orchestrator routing hints).

## Inputs

- **input-id** — description of each required input (run id, site context, …).

## Outputs

- **output-id** — packaged findings, Evidence ids, remediation plan draft, …
- Note which outputs require Human review before they are final.

## Skills invoked

Ordered list of Skills with conditions:

1. `skill-a` — when / why
2. `skill-b` — when / why (depends on skill-a Evidence …)

Cross-pillar composition is expected; path ownership stays on each Skill.

## Evidence

How this Agent aggregates or references Skill Evidence. Decision log entries
must include `evidence_ids`. Do not invent metrics when Connectors fail — keep
dependent claims at `needs_human_verification`.

## Human review points

Where the workflow stops for human approval (maps to `human_review_gate`):

- After Evidence is packaged / prioritised
- Before any remediation plan is marked final
- Before any live-site or CMS mutation proposal proceeds

The Orchestrator enforces the stop; this section declares *when* the gate fires.

## Cost

Match `cost_model`. Document `cost_drivers` and `unit_estimates` labelled as
estimates. No fake precision. Exact figures may wait for the P5 metrics helper.

## Procedure / workflow

1. Numbered end-to-end steps.
2. Call out Decision log writes (routing context is Orchestrator-owned; in-workflow
   decisions are this Agent’s).
3. Call out Human review points by step number.
