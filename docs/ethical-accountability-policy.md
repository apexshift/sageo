# Ethical accountability policy

## Purpose / audience

This policy binds everyone who builds, runs, or extends SageO: maintainers, practitioners, and (after public release) external contributors. It turns the master ethics locks into enforceable prose: white-hat only, Evidence for claims, Human review before live change, read-only Connectors through P5, and accountable Decision logs.

Tone and positioning stay plain and practitioner-first. Do not promise guaranteed rankings, autonomous publishing, or set-and-forget live-site changes.

## White-hat only; prohibited practices

SageO Skills and Agents exist to help practitioners improve search performance honestly and consistently. Prohibited:

- Scaled content abuse, doorway pages, cloaking, or other manipulative tactics aimed at deceiving search or answer engines
- Inventing metrics, fabricating Evidence, or backfilling confidence when a source failed
- Framing outcomes as “guaranteed rankings” or similar hype
- Auto-publishing or mutating a live site without a Human review gate and recorded approval
- Shipping Skills that mutate live sites while declaring `human_review_gate: not_required`

Maintainers reject contributions and run configurations that violate these rules.

## Evidence requirements

Every factual claim emitted by a Skill, Agent, or Orchestrator must be backed by Evidence:

- Required: `claim`, `source`, `observed_at`, `confidence`
- When `confidence` is `needs_human_verification`: also `verification_reason`
- Optional: `method`, `raw_ref`

Skill packages declare `evidence_requirement` (`full` | `partial` | `none`):

- **full** — every emitted claim is Evidence
- **partial** — procedural bits may be claim-free; any claim still needs Evidence
- **none** — no factual claims (rare); emitting claims with `none` is a reject

On connector auth failure, rate limit, timeout, or empty/error payload: do not invent metrics. Emit Evidence with `needs_human_verification`, `source` = connector + operation, and an appropriate `verification_reason`. Dependent claims stay at `needs_human_verification`; non-dependent paths may continue.

## Human review gates & no live mutation without approval

Nothing publishes to or mutates a live site without a Human review gate and recorded human approval in the Decision log.

Two layers:

1. Agents declare when a gate is required (`human_review_gate` and **Human review points** in `AGENT.md`).
2. The Orchestrator enforces the stop — work does not proceed past a required gate without approval.

Diagnose-only Skills and finding-only Agent steps may use `not_required` when they emit no remediation that could affect a live site. Any remediation plan marked final, CMS write, GBP edit proposal, or other live-site mutation proposal requires `required`.

## Connector read-only posture (through P5)

Connectors are MCP server packs under `connectors/`. Through P5 they are **read-only**. Credentials come from environment variables only (see `.env.example`); never commit secrets. Missing required env → the Connector refuses to start and emits Evidence with `needs_human_verification` and `verification_reason: missing_credentials`.

Any future write or mutation capability requires a new map Decision and a Human review gate per mutation. Skills consume Connector tools; they do not embed vendor SDKs.

## Decision logging / accountability

Every Agent or Orchestrator decision that routes work, prioritises a queue, sequences Agents, or handles a Human review gate writes an append-only Decision log entry under `runs/<id>/`. Required shape includes `decision_id`, actor (`agent` or `orchestrator`), timestamp, inputs reference, skills invoked, outcome, evidence ids, human_review status, and rationale.

No in-place edits. Corrections are new entries that supersede prior ids. Retention for P1–P5 is “keep with the run”; archive or delete is an operator choice later. Chat transcripts are not Decision logs.

## Reporting misuse / maintainer enforcement

Report suspected misuse (policy violations in Skills, Agents, Connectors, or published runs) to the repository maintainers via a GitHub issue labelled for maintainer attention, or privately if disclosure would cause harm.

Maintainers may:

- Reject or revert contributions that violate this policy
- Disable or remove Skills/Agents that mutate live sites without gates
- Refuse “guaranteed rankings” framing and fabricated Evidence
- Defer or close issues that ask for write scopes before a new map Decision

This policy is part of P1 Foundation & governance. Later phases deepen enforcement in code (contract lint, Orchestrator gate stops, CI) without weakening these rules.
