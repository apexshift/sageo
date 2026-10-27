---
name: example-skill
description: >-
  One-sentence what it does and when to use it. Keep under a few lines;
  detail belongs in Purpose and Procedure.
metadata:
  version: "0.1.0"
  capability_pillar: technical-foundation
  primary_outcome: SEO
  secondary_outcomes: AIO, GEO
  evidence_requirement: full
  human_review_gate: not_required
  inputs: page-html
  outputs: findings, evidence
  # connectors: gsc,ga4
  # tags: schema, structured-data
---

<!--
  Copy to skills/<pillar-slug>/<skill-name>/SKILL.md
  - name MUST equal the directory name
  - capability_pillar MUST equal the parent folder slug
  - capability_pillar ∈ technical-foundation | content-answer-quality |
    authority-trust | measurement-prioritisation | local-geographic
  - primary_outcome ∈ SEO | AIO | GEO
  - evidence_requirement ∈ full | partial | none
  - human_review_gate ∈ required | not_required
  Optional metadata: secondary_outcomes, inputs, outputs, connectors, tags,
  plus agentskills license / compatibility.
  Optional body: Connectors, Examples, Failure modes.
  Optional dirs: scripts/, references/, assets/
-->

## Purpose

What this Skill does and why. One capability pillar; findings stay Skill-level.
Remediations that could affect a live site belong to Agents / Orchestrator.

## Inputs

- **input-id** — description of each required input (types, fixtures, or refs).
- Document detailed schemas here or under `references/`.

## Outputs

- **output-id** — description of each output (findings shape, Evidence list, …).
- If there is an executable entry point, name it (e.g. `scripts/run.py`).

## Evidence

State how `evidence_requirement` applies. For `full`, every claim is an Evidence
record with `claim`, `source`, `observed_at`, `confidence`, and
`verification_reason` when confidence is `needs_human_verification`.

## Human review

State whether `human_review_gate` is `required` or `not_required` and why.
Finding-only Skills typically use `not_required`; anything that proposes or
applies a live-site change must use `required` (usually at Agent level).

## Procedure

1. Numbered steps the runtime or human follows.
2. Include failure / `needs_human_verification` branches (missing source, parse error, contradiction).
3. No live API calls inside hermetic tests; Connectors are separate MCP packs.
