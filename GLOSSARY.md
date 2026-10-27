# SageO

SageO is a collection of agents and agent skills for repetitive, consistent search optimisation at local, national, and global reach, aligned to SEO, AIO, and GEO outcomes.

## Language

**SageO**:
The product and repository: agents plus agent skills for consistent search optimisation across local, national, and global reach.
_Avoid_: sageio, seo-agents-skills

**Skill**:
An atomic, single-task module that belongs to one capability pillar. On disk: `skills/<pillar-slug>/<skill-name>/SKILL.md` (optional `scripts/`, `references/`, `assets/`).
_Avoid_: tool (when you mean a Skill), plugin, README-as-contract

**Agent**:
A workflow-oriented coordinator that composes Skills from one or more capability pillars. On disk: `agents/<agent-name>/AGENT.md`.
_Avoid_: bot, assistant (when you mean an Agent in this system)

**Orchestrator**:
The layer above Agents that routes and prioritises work, sequences multi-agent flows, and **enforces** Human review gates. Agents declare gates; the Orchestrator owns the stop. On disk: `orchestrator/ORCHESTRATOR.md`.
_Avoid_: router (when you mean the full Orchestrator), agent (when you mean Orchestrator), Agents routing to other Agents

**Capability pillar**:
One of the five Skill organisation axes: Technical Foundation, Content & Answer Quality, Authority & Trust, Measurement & Prioritisation, Local / Geographic.
_Avoid_: SEO pillar, AIO pillar, GEO pillar (those are Outcome pillars)

**Outcome pillar**:
One of SEO, AIO, or GEO — the outcome framing for what SageO optimises for.
_Avoid_: capability pillar names used as outcome labels

**SEO**:
Classic search-engine / SERP performance as an Outcome pillar.
_Avoid_: using SEO as a capability-pillar or folder name

**AIO**:
Answer-engine, AI-overview, and LLM-cited-answer performance as an Outcome pillar.
_Avoid_: using AIO as a capability-pillar or folder name

**GEO**:
Generative engine optimisation as an Outcome pillar (generative-specific slice).
_Avoid_: geographic, local reach (those are Reach or the Local / Geographic capability pillar)

**Reach**:
The local, national, or global scope of a piece of work. Not an Outcome pillar.
_Avoid_: GEO (when you mean geographic scope)

**Evidence**:
A structured claim record with `claim`, `source`, `observed_at`, and `confidence` (`high` | `medium` | `low` | `needs_human_verification`). When confidence is `needs_human_verification`, include `verification_reason`.
_Avoid_: proof, citation (when you mean the Evidence contract)

**Decision log**:
An append-only record of an Agent or Orchestrator decision (`decision_id`, actor, inputs, skills, outcome, evidence_ids, human_review, rationale), stored under a Run directory.
_Avoid_: chat transcript (when you mean the Decision log)

**Run directory**:
A per-run folder (`runs/<id>/`) holding append-only Evidence and Decision log artifacts for that execution.
_Avoid_: treating the git repo history as the run log

**Human review gate**:
A hard stop that requires human approval before any live-site change or before a remediation plan is finalised.
_Avoid_: soft warning, optional review

**Connector**:
A read-only (through P5) MCP server pack that exposes a third-party data system (GSC, GA4, or a crawl/SERP class) to Skills. Credentials via environment variables only.
_Avoid_: Skill (when you mean a Connector), embedding vendor SDKs inside Skills
