# Research: Run, Decision log, and Human review gate surfaces the GUI must mirror

**Ticket:** [#144](https://github.com/apexshift/sageo/issues/144)  
**Branch:** `research/run-decision-gate-gui-surfaces`  
**Parent map:** [#142](https://github.com/apexshift/sageo/issues/142) (Operator desktop GUI product/UX spec)  
**Scope:** Catalogue the **shipped** artifacts, fields, and state transitions a desktop operator GUI must read and write to start/configure a Run, show progress, browse findings/Evidence, and approve/reject Human review gates — **without inventing a parallel model**. Research only; no GUI build.

**Product filter:** Orchestrator owns sequencing and the system stop; Agents declare gates and compose Skills; Evidence + Decision logs are append-only under `runs/<id>/`; ethics forbid auto-approve and live mutation without recorded Human approval.

**Method:** Primary sources are this repo — `GLOSSARY.md`, `docs/architecture.md`, `orchestrator/ORCHESTRATOR.md`, `agents/*/AGENT.md`, `src/sageo/orchestrator/runtime.py`, `src/sageo/agents/runtime.py`, `src/sageo/metrics.py`, `src/sageo/connectors/nhv.py`, `tests/orchestrator/*`, `tests/agents/test_run_workflow.py`, `tests/e2e/national-audit/*`, `docs/examples/*`, `docs/ethical-accountability-policy.md`.

---

## 1. Answer in one page

| GUI job | Mirror these shipped surfaces (do not invent alternatives) |
| --- | --- |
| **Start / configure a Run** | Orchestrator `RunRequest` fields → `run(...)`; or Agent `run_agent(...)` with `inputs` + optional `skill_names`. Agent roster comes from `agents/*/AGENT.md` (+ in-process `AgentSpec` for Orchestrator). |
| **Show progress** | `runs/<id>/state.json` (`gate_state`, `agent_statuses` / Agent `status`, `schedule`/`next_index`/`paused_agent`, `skills_invoked`). Poll/tail; no separate progress API exists. |
| **Browse findings / Evidence** | `runs/<id>/evidence.jsonl` (+ nested `agents/<name>/evidence.jsonl` when composed). Link via Decision log `evidence_ids`. Optional `metrics.json` for completeness, not rankings. |
| **Approve / reject gates** | When `gate_state == awaiting_approval`, call `resume(..., approved=bool)` and/or `resume_agent(..., approved=bool)`. Both append a Decision log gate entry; neither edits prior rows. |

**Canonical on-disk layout today** (`runs/<id>/`, contents gitignored):

```text
runs/<id>/
├── state.json              # mutable snapshot (rewritten)
├── decision_log.jsonl      # append-only
├── evidence.jsonl          # append-only
├── metrics.json            # optional (write_run_metrics)
├── invocations.json        # optional (feeds metrics)
└── agents/<agent-name>/    # nested Agent runs (e2e / composition pattern)
    ├── state.json
    ├── decision_log.jsonl
    └── evidence.jsonl
```

Public Python seams: `sageo.orchestrator.run` / `resume`; `sageo.agents.run_agent` / `resume_agent`; `sageo.metrics.write_run_metrics`.

---

## 2. Start / configure a Run

### 2.1 Orchestrator inputs — `RunRequest`

From [`src/sageo/orchestrator/runtime.py`](../../src/sageo/orchestrator/runtime.py) and [`orchestrator/ORCHESTRATOR.md`](../../orchestrator/ORCHESTRATOR.md):

| Field | Type / domain | Required | Notes for GUI |
| --- | --- | --- | --- |
| `goal` | `str` | Yes | Free-text practitioner goal |
| `intent` | `str` | Yes | Matched against Agent `when_to_use` (unless `playbook` drives schedule) |
| `primary_outcome` | `SEO` \| `AIO` \| `GEO` | Yes | Must match Agent `primary_outcome` for intent routing |
| `property_refs` | `Mapping[str, str]` | Yes | e.g. `{"site": "https://example.com/"}` |
| `reach` | `local` \| `national` \| `global` \| omit | No | Filters Agents that declare `reach` |
| `playbook` | e.g. `thin_audit` \| omit | No | `thin_audit` → Technical → Content/AIO → Measurement by `pipeline_role` |

Also required at the call site (not on `RunRequest`): `agents: Sequence[AgentSpec]`, `runs_root: Path`, `observed_at: str` (ISO timestamp), optional `run_id`.

**GUI configure surface:** form/editor for the six `RunRequest` fields + choice of Agents / playbook. Do not invent a separate “job” schema — persist the same dict that lands in `state.json` → `request`.

### 2.2 Orchestrator `AgentSpec` (in-process roster)

| Field | Role |
| --- | --- |
| `name` | Agent identity (matches `AGENT.md` `name` when composed) |
| `primary_outcome` | Routing |
| `when_to_use` | Intent set |
| `reach` | Optional Reach filter |
| `human_review_gate` | `required` \| `not_required` — Orchestrator may stop **before** `execute` |
| `severity` / `impact` | Optional 1–5; when all scheduled Agents have both → severity×impact priority |
| `pipeline_role` | `technical` \| `content_aio` \| `measurement` for `thin_audit` |
| `execute` | Callable returning `{evidence_ids, status, ...}` |

Shipped Agent contracts (read for labels / defaults, not a second model):

| Agent | `human_review_gate` | `primary_outcome` | Skills (declared order) |
| --- | --- | --- | --- |
| `technical-findings` | `not_required` | SEO | crawl-issue-extractor → indexability-checker → schema-validator → cwv-scorer |
| `content-aio` | `required` | AIO | intent-classifier → answer-extractability-scorer → entity-coverage-checker → citation-opportunity-identifier |
| `measurement-evidence` | `required` | SEO | mention-sentiment-screener → severity-impact-scorer → evidence-packager |
| `local-reach` | `required` | SEO | gbp-profile-auditor → local-schema-checker → citation-consistency-checker |

### 2.3 Agent-only start — `run_agent`

From [`src/sageo/agents/runtime.py`](../../src/sageo/agents/runtime.py):

| Call arg | Notes |
| --- | --- |
| `agent_dir` | Directory with `AGENT.md` |
| `skill_stubs` | Injected Skill callables (harness); a GUI host would supply real Skill runners |
| `runs_root` | Parent of `runs/<id>/` |
| `observed_at` | Timestamp stamped into Decision log |
| `run_id` | Optional; else UUID |
| `inputs` | Opaque `Mapping` merged into Decision log `inputs` (Agent-specific; see e2e `agent_inputs.json`) |
| `skill_names` | Optional subset; still executed in **declared** `AGENT.md` order. Else optional `scripts/select_skills.py` |

**Unknown Orchestrator intent:** no Agent invented — NHV Evidence + Decision log `outcome: ask_human`, `human_review: awaiting_approval`, but `gate_state: closed` (ask-human is not the same resume path as a gate stop). GUI should surface that Evidence and prompt the operator, not call `resume`.

---

## 3. Run directory artifacts (file shapes)

### 3.1 `state.json` — Orchestrator

Rewritten by `_write_state`. Observed fields:

```json
{
  "request": {
    "goal": "...",
    "intent": "...",
    "primary_outcome": "SEO",
    "property_refs": {"site": "https://example.com/"},
    "reach": "national",
    "playbook": "thin_audit"
  },
  "schedule": ["technical-findings", "content-aio", "measurement-evidence"],
  "next_index": 2,
  "paused_agent": "measurement-evidence",
  "gate_state": "awaiting_approval",
  "agent_statuses": [
    {"name": "technical-findings", "status": "completed"},
    {"name": "content-aio", "status": "completed"},
    {"name": "measurement-evidence", "status": "awaiting_human_review"}
  ],
  "evidence_refs": ["ev-...", "..."]
}
```

| Field | Values / meaning |
| --- | --- |
| `gate_state` | `awaiting_approval` \| `closed` |
| `agent_statuses[].status` | From execute / gate stop: typically `completed`, `awaiting_human_review` (rejection leaves paused Agent still listed as `awaiting_human_review` with gate closed) |
| `next_index` | Index into `schedule` for resume continuation |
| `paused_agent` | Name of gated Agent; `null` when closed |
| `evidence_refs` | Ordered Evidence id strings collected across Agents |

### 3.2 `state.json` — Agent

```json
{
  "agent_name": "measurement-evidence",
  "agent_dir": "/abs/path/to/agents/measurement-evidence",
  "skills_invoked": ["mention-sentiment-screener", "severity-impact-scorer", "evidence-packager"],
  "evidence_ids": ["ev-...", "..."],
  "gate_state": "awaiting_approval",
  "status": "awaiting_human_review",
  "inputs": { "...": "..." },
  "human_review_gate": "required"
}
```

| `status` | When |
| --- | --- |
| `awaiting_human_review` | Gate required; Skills done; waiting |
| `completed` | Finished (`not_required` or approved) |
| `rejected` | `resume_agent(..., approved=False)` |

### 3.3 `decision_log.jsonl` — append-only rows

Required accountability shape ([`GLOSSARY.md`](../../GLOSSARY.md), ethics policy, ORCHESTRATOR.md, runtimes):

| Field | Required | Notes |
| --- | --- | --- |
| `decision_id` | Yes | Stable id; corrections = **new** rows (no in-place edit) |
| `actor` | Yes | `orchestrator` \| `agent` |
| `timestamp` | Yes | From `observed_at` |
| `inputs` | Yes | Object (request slice, `{approved, agent}`, etc.) |
| `skills` | Yes | List (may be `[]` on Orchestrator routing) |
| `outcome` | Yes | Kind-specific string |
| `evidence_ids` | Yes | List of Evidence ids |
| `human_review` | Yes | See §5 |
| `rationale` | Yes | Human-readable |

**Also written by shipped runtimes** (GUI should display; treat as part of the live shape):

| Field | Notes |
| --- | --- |
| `kind` | `routing` \| `prioritisation` \| `schedule` \| `gate` \| `agent_workflow` |
| `agents` | Orchestrator entries: Agent name list |

**Illustrative Orchestrator kinds / outcomes:**

| `kind` | Typical `outcome` | Typical `human_review` |
| --- | --- | --- |
| `routing` | `scheduled` \| `ask_human` | `not_required` \| `awaiting_approval` |
| `prioritisation` | `ordered` | `not_required` |
| `schedule` | `sequential` | `not_required` |
| `gate` (stop) | `awaiting_approval` | `awaiting_approval` |
| `gate` (resume) | `approved` \| `rejected` | `approved` \| `rejected` |

**Illustrative Agent kinds / outcomes:**

| `kind` | Typical `outcome` | Typical `human_review` |
| --- | --- | --- |
| `agent_workflow` | `skills_completed` (then gate) \| `completed` | `pending` \| `not_required` |
| `gate` (stop) | `awaiting_approval` | `awaiting_approval` |
| `gate` (resume) | `approved` \| `rejected` | `approved` \| `rejected` |

### 3.4 `evidence.jsonl` — append-only rows

Contract ([`docs/architecture.md`](../architecture.md), ethics policy):

| Field | Required | Domain |
| --- | --- | --- |
| `claim` | Yes | Factual claim text |
| `source` | Yes | Provenance string (fixture, connector `pack/tool`, stub, …) |
| `observed_at` | Yes | Timestamp |
| `confidence` | Yes | `high` \| `medium` \| `low` \| `needs_human_verification` |
| `verification_reason` | When `confidence == needs_human_verification` | Connector-locked set below; Skills may use other reasons for judgmental NHV |
| `method` | No | How derived |
| `raw_ref` | No | Pointer to raw artifact |
| `id` | De facto for linking | Referenced by Decision log `evidence_ids` / Orchestrator `evidence_refs` |

Connector NHV reasons ([`src/sageo/connectors/nhv.py`](../../src/sageo/connectors/nhv.py)):  
`missing_credentials` \| `auth_failed` \| `rate_limited` \| `timeout` \| `upstream_error` \| `empty_result`.

GUI browse: render JSONL rows; filter NHV; deep-link from Decision log `evidence_ids`. Do not invent a parallel “Finding” table that drops Evidence fields — Skill “findings” in goldens are Skill-local outputs; the Run’s durable browse surface is Evidence (+ Decision log references).

### 3.5 Optional `metrics.json` / `invocations.json`

[`write_run_metrics`](../../src/sageo/metrics.py) reads `evidence.jsonl`, `decision_log.jsonl`, optional `invocations.json`, writes:

```json
{
  "cost": {
    "cost_models": ["tokens_and_connector_calls", "tokens_only"],
    "tokens_class": "from_usage_stub",
    "connector_calls_class": "...",
    "tokens_estimate": null,
    "connector_calls_estimate": null,
    "invocation_count": 3,
    "uncertainty_notes": ["..."]
  },
  "evidence_completeness": {
    "status": "pass",
    "pass_count": 0,
    "fail_count": 0,
    "missing_evidence_ids": [],
    "nhv_missing_verification_reason": []
  }
}
```

Never invent ranking/traffic KPIs. GUI may show cost class + completeness; must not fabricate SEO metrics.

### 3.6 Nested `agents/<name>/`

National-audit e2e composition ([`tests/e2e/national-audit/test_e2e.py`](../../tests/e2e/national-audit/test_e2e.py)): each Agent run uses `run_id=<agent-name>` under `runs/<orch-id>/agents/`. Orchestrator Decision/Evidence at the root are merged from Agent artifacts. GUI progress for a full audit should show **both** root Orchestrator `state.json` and nested Agent states.

---

## 4. Progress: what to poll

There is **no** event bus or websocket in-tree. Progress = filesystem + in-memory `RunResult` / `AgentRunResult` from the last call.

| Surface | Progress signal |
| --- | --- |
| Orchestrator `RunResult` | `run_id`, `agent_statuses`, `evidence_refs`, `gate_state`, `decision_log_path`, `run_dir`, `evidence` |
| Agent `AgentRunResult` | `run_id`, `agent_name`, `skills_invoked`, `evidence_ids`, `gate_state`, `status`, paths, `evidence` |
| On disk | Tail `decision_log.jsonl`; re-read `state.json`; grow `evidence.jsonl` |

**AFK pattern** ([`docs/examples/afk-automation.md`](../examples/afk-automation.md)): run unattended until `gate_state == awaiting_approval` (or Agent `status == awaiting_human_review`) → notify human (ops layer, not shipped) → `resume` / `resume_agent`.

---

## 5. Human review gate — stop / resume path (as shipped)

### 5.1 Two layers (do not collapse)

1. **Agent declares** `metadata.human_review_gate: required | not_required` (+ body **Human review points**).
2. **Orchestrator owns the stop** — nothing proceeds past a required gate without Decision log approval (`human_review: approved`). Gates are never skipped for cost ([`ORCHESTRATOR.md`](../../orchestrator/ORCHESTRATOR.md), ethics policy).

### 5.2 Orchestrator stop conditions

From `_execute_from` / tests:

1. **Pre-execute gate:** AgentSpec `human_review_gate == required` and this Agent is not the one just approved → append `kind: gate`, `outcome: awaiting_approval`, set `gate_state: awaiting_approval`, `paused_agent`, `next_index` = current index, **do not call** `execute`.
2. **Post-execute gate:** `execute` returns `status: awaiting_human_review` → same stop after collecting `evidence_ids` (Agent Skills already ran — Measurement package gate pattern in national-audit e2e).

### 5.3 Orchestrator resume — `resume(run_id, agents, *, runs_root, approved, observed_at)`

Preconditions: `state.json` `gate_state == awaiting_approval` (else `ValueError`).

| `approved` | Behavior |
| --- | --- |
| `True` | Append gate resume (`human_review: approved`, `outcome: approved`); continue `_execute_from` at `next_index`, with `gate_approved_for=paused_agent` so that Agent may run; strip prior `awaiting_human_review` status for that Agent before re-executing. |
| `False` | Append gate resume (`rejected`); set `gate_state: closed`, `paused_agent: null`; **do not** run the gated Agent / continuation. Statuses left as at pause. |

Decision log alone must reconstruct stop→resume order (asserted in `tests/orchestrator/test_run_gate.py`).

### 5.4 Agent stop / resume — `run_agent` / `resume_agent`

When `human_review_gate: required`, after all Skills:

1. Append `agent_workflow` with `outcome: skills_completed`, `human_review: pending`.
2. Append `gate` with `outcome` / `human_review: awaiting_approval`.
3. Return `status: awaiting_human_review`, `gate_state: awaiting_approval`.

`resume_agent(run_id, *, runs_root, approved, observed_at)`:

| `approved` | Result `status` | Decision `human_review` / `outcome` |
| --- | --- | --- |
| `True` | `completed` | `approved` |
| `False` | `rejected` | `rejected` |

Both close `gate_state: closed`. Skills are **not** re-run on Agent resume (unlike Orchestrator resume, which re-enters `execute` for the paused Agent).

### 5.5 Dual-gate composition (national audit)

E2e pattern operators/GUIs must understand:

- Nested Agent may pause (`content-aio`, `measurement-evidence` declare `required`).
- Composition may **auto-clear** an intermediate Agent gate inside `execute` (test-only convenience for content-aio) so the **Orchestrator-visible** stop is Measurement’s `awaiting_human_review`.
- Operator approval for the system package gate is Orchestrator `resume(approved=True)`, which re-enters Measurement `execute`; that path then `resume_agent` on the nested Agent if its `state.json` is still `awaiting_approval`.

A GUI that only calls `resume_agent` on the root run id will miss Orchestrator schedule state. Mirror **both** seams when presenting a multi-agent Run.

### 5.6 What the GUI must write for approval

**Write path = runtime call**, which appends Decision log + rewrites `state.json`. Do not hand-edit JSONL to fake `human_review: approved`. Do not set `approved=True` from a bot without a real human ([`afk-automation.md`](../examples/afk-automation.md)).

Minimum operator action payload today: `{ run_id, approved: bool }` (+ `observed_at`, `runs_root`, and the same `agents` roster for Orchestrator resume).

---

## 6. GUI read/write matrix (no parallel model)

| Concern | READ | WRITE |
| --- | --- | --- |
| Configure Run | `agents/*/AGENT.md`, `orchestrator/ORCHESTRATOR.md`, glossary domains | Call `run` / `run_agent` with `RunRequest` / `inputs` |
| List / open Runs | `runs/*/` directories | Create only via runtime (`run_dir.mkdir`) |
| Progress | `state.json`, growing JSONL, last `RunResult` | — |
| Evidence / findings | `evidence.jsonl` (+ nested) | Only via Skill/Agent execution (GUI does not author claims) |
| Decision audit | `decision_log.jsonl` | Only via runtime appends |
| Gate approve/reject | `gate_state`, gate Decision rows, nested Agent state | `resume` / `resume_agent` |
| Cost / completeness | `metrics.json` | Optional `write_run_metrics` (+ optional `invocations.json`) |

**Out of scope / do not invent:** chat transcript as Decision log; soft “warnings” instead of gates; auto-publish; ranking/traffic KPIs; a second persistence schema beside `runs/<id>/`.

---

## 7. Implications for map #142 (pointers only)

- Operator desktop UX should treat **`runs/<id>/` JSON/JSONL + `run`/`resume` APIs** as the product model.
- Gate UX is a hard stop on `awaiting_approval` with binary approve/reject that maps 1:1 to `approved: bool`.
- Progress UX is schedule + per-Agent status from `state.json`, not a custom workflow engine.
- Findings browser = Evidence contract fields; NHV rows need verification UI, not silent confidence upgrades.

---

## Sources (repo)

- [`GLOSSARY.md`](../../GLOSSARY.md) — Evidence, Decision log, Run directory, Human review gate  
- [`docs/architecture.md`](../architecture.md) — layers, Run artifacts, two-layer gates  
- [`docs/ethical-accountability-policy.md`](../ethical-accountability-policy.md) — Evidence + Decision log + no live mutation  
- [`orchestrator/ORCHESTRATOR.md`](../../orchestrator/ORCHESTRATOR.md) — routing, priority, gate ownership  
- [`agents/*/AGENT.md`](../../agents/) — declared gates, skills, inputs/outputs  
- [`src/sageo/orchestrator/runtime.py`](../../src/sageo/orchestrator/runtime.py) — `RunRequest`, `run`, `resume`, state shape  
- [`src/sageo/agents/runtime.py`](../../src/sageo/agents/runtime.py) — `run_agent`, `resume_agent`, state shape  
- [`src/sageo/metrics.py`](../../src/sageo/metrics.py) — `metrics.json`  
- [`src/sageo/connectors/nhv.py`](../../src/sageo/connectors/nhv.py) — NHV reason set  
- [`tests/orchestrator/test_run_gate.py`](../../tests/orchestrator/test_run_gate.py) — stop/resume/reject  
- [`tests/agents/test_run_workflow.py`](../../tests/agents/test_run_workflow.py) — Agent Decision log + gate  
- [`tests/e2e/national-audit/`](../../tests/e2e/national-audit/) — nested Agents + Measurement package gate  
- [`docs/examples/national-audit.md`](../examples/national-audit.md), [`afk-automation.md`](../examples/afk-automation.md) — artifact list + ops loop  
