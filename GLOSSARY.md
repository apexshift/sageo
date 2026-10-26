# SageO

SageO is a collection of agents and agent skills for repetitive, consistent search optimisation at local, national, and global reach, aligned to SEO, AIO, and GEO outcomes.

## Language

**SageO**:
The product and repository: agents plus agent skills for consistent search optimisation across local, national, and global reach.
_Avoid_: sageio, seo-agents-skills

**Skill**:
An atomic, single-task module that belongs to one capability pillar.
_Avoid_: tool (when you mean a Skill), plugin

**Agent**:
A workflow-oriented coordinator that composes Skills from one or more capability pillars.
_Avoid_: bot, assistant (when you mean an Agent in this system)

**Orchestrator**:
The layer above Agents that handles routing, prioritisation, and human review gates.
_Avoid_: router (when you mean the full Orchestrator), agent (when you mean Orchestrator)

**Capability pillar**:
One of the five Skill organisation axes: Technical Foundation, Content & Answer Quality, Authority & Trust, Measurement & Prioritisation, Local / Geographic.
_Avoid_: SEO pillar, AIO pillar, GEO pillar (those are Outcome pillars)

**Outcome pillar**:
One of SEO, AIO, or GEO — the outcome framing for what SageO optimises for.
_Avoid_: capability pillar names used as outcome labels

**Evidence**:
A source plus timestamp on a claim, or an explicit “needs human verification” flag.
_Avoid_: proof, citation (when you mean the Evidence contract)

**Human review gate**:
A hard stop that requires human approval before any live-site change or before a remediation plan is finalised.
_Avoid_: soft warning, optional review
