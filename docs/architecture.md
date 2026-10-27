# Architecture

## Purpose & master map

SageO is a hybrid Markdown + Python collection of Skills, Agents, and an Orchestrator for repetitive, consistent search optimisation across local, national, and global Reach, framed around SEO, AIO, and GEO outcomes.

This document orients newcomers to the layers, pillars, layout, Evidence model, and Human review gates. It does not restate every master Decision. Authoritative locks live on the [Master map: SageO five-phase bootstrap](https://github.com/apexshift/sageo/issues/1) and the phase locked-spec handoffs under `docs/handoffs/`. Domain language lives in root `GLOSSARY.md`.

## System layers

SageO has four composition layers:

| Layer | Role | On disk |
| --- | --- | --- |
| **Skill** | Atomic, single-task module in one capability pillar. Emits findings and Evidence. | `skills/<pillar-slug>/<skill-name>/SKILL.md` |
| **Agent** | Workflow coordinator that composes Skills from one or more pillars. Declares review points and cost. | `agents/<agent-name>/AGENT.md` |
| **Orchestrator** | Routes and prioritises work, sequences multi-agent flows, and **enforces** Human review gates. Agents declare gates; the Orchestrator owns the stop. | `orchestrator/ORCHESTRATOR.md` |
| **Connector** | Read-only MCP server pack that exposes a third-party data system to Skills. Credentials via environment variables only. | `connectors/` |

Agents never route to other Agents — only the Orchestrator does. Skills consume Connector tools; they do not embed vendor SDKs. Shared Python that two or more packages need lives under `src/sageo/`; Skill-local helpers stay in that Skill’s `scripts/`.

## Capability vs Outcome pillars (+ Reach)

**Capability pillars** organise Skills on disk (folder slugs in parentheses):

1. Technical Foundation (`technical-foundation`)
2. Content & Answer Quality (`content-answer-quality`)
3. Authority & Trust (`authority-trust`)
4. Measurement & Prioritisation (`measurement-prioritisation`)
5. Local / Geographic (`local-geographic`)

**Outcome pillars** frame what SageO optimises for: **SEO** (classic SERP), **AIO** (answer engines / AI overviews / LLM-cited answers), **GEO** (generative engine optimisation). Every Skill declares exactly one `primary_outcome` and may list `secondary_outcomes`. Catalogue and docs group by capability pillar first; outcome tags are filters, not folders. Never name a folder SEO, AIO, or GEO.

**Reach** is the local, national, or global scope of a piece of work. Reach is not an Outcome pillar and is not the meaning of GEO.

## Repository layout

```text
sageo/
├── AGENTS.md, GLOSSARY.md, README.md
├── docs/            # agents/, handoffs/, research/, templates/, governance prose
├── skills/          # capability-pillar library (source of truth)
├── agents/          # Agent contracts
├── orchestrator/    # Orchestrator contract + policy
├── connectors/      # MCP server packs
├── src/sageo/       # shared Python library
├── runs/            # local run artifacts (gitignored contents)
└── tests/
```

Governance prose lives at `docs/architecture.md`, `docs/ethical-accountability-policy.md`, and `docs/contribution-guidelines.md`. `docs/adr/` may appear later when Architecture Decision Records are recorded.

Skill path: `skills/<pillar-slug>/<skill-name>/` with required `SKILL.md`. Optional conventional subdirs: `scripts/`, `references/`, `assets/`. Directory name equals frontmatter `name`. No parallel `skill.yaml`; no README-as-contract.

Copy-ready contracts: `docs/templates/SKILL.md` and `docs/templates/AGENT.md`.

## Evidence, Decision logs, Run directory

Every factual claim carries **Evidence** with required fields `claim`, `source`, `observed_at`, and `confidence` (`high` | `medium` | `low` | `needs_human_verification`). When confidence is `needs_human_verification`, include `verification_reason`. Optional fields: `method`, `raw_ref`.

`needs_human_verification` is allowed when a source is missing, inaccessible, contradictory, or outside connector scope — never as a shortcut to skip a fetch that was possible — or for inherently judgmental calls even when data exists.

Agents and the Orchestrator write append-only **Decision log** entries (`decision_id`, actor, timestamp, inputs, skills, outcome, evidence_ids, human_review, rationale). Artifacts live under a **Run directory** `runs/<id>/` as JSON/JSONL. No in-place edits; corrections are new entries that supersede prior ids. `runs/` contents are gitignored; keep the placeholder committed.

## Human review gates (two layers)

1. **Agent layer** — the Agent declares *when* a gate is needed (`human_review_gate` plus body **Human review points**).
2. **Orchestrator layer** — the Orchestrator owns the system stop: nothing proceeds past a required gate without recorded human approval in the Decision log.

Remediation plans that could affect a live site, and any live-site mutation, require a Human review gate. Skills that only report findings may set `human_review_gate: not_required`; remediations remain Agent/Orchestrator concerns.

## Phase roadmap (P1–P5)

| Phase | Focus |
| --- | --- |
| **P1** | Foundation & governance — tree, harness, templates, one template Skill, README, ethics |
| **P2** | Core Skill library under the five capability pillars |
| **P3** | Data connections (GSC, GA4, crawl/SERP MCP packs) and audit Orchestrator |
| **P4** | Reference Agents composing Skills into workflows |
| **P5** | Quality metrics, packaging, CI, public-release CONTRIBUTING |

Detail for each phase lives in `docs/handoffs/` and the linked Spec issues on the master map.
