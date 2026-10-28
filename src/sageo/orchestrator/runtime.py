"""Black-box Orchestrator run seam.

``run`` / ``resume`` are the public interface. Fake in-process Agents are
passed as ``AgentSpec`` values (P4 owns real ``AGENT.md`` identities).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from sageo.connectors.nhv import nhv_evidence

GateLiteral = Literal["required", "not_required"]
PipelineRole = Literal["technical", "content_aio", "measurement"]

THIN_AUDIT_ORDER: tuple[PipelineRole, ...] = (
    "technical",
    "content_aio",
    "measurement",
)


@dataclass(frozen=True)
class AgentSpec:
    """In-process Agent description for Orchestrator tests and runtime."""

    name: str
    primary_outcome: str
    when_to_use: frozenset[str]
    reach: frozenset[str] | None = None
    human_review_gate: GateLiteral = "not_required"
    severity: int | None = None
    impact: int | None = None
    pipeline_role: PipelineRole | None = None
    execute: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None


@dataclass(frozen=True)
class RunRequest:
    """Practitioner run inputs (locked Inputs sketch)."""

    goal: str
    intent: str
    primary_outcome: str
    property_refs: Mapping[str, str]
    reach: str | None = None
    playbook: str | None = None


@dataclass
class RunResult:
    """Orchestrator outputs (locked Outputs sketch)."""

    run_id: str
    agent_statuses: list[dict[str, str]]
    evidence_refs: list[str]
    gate_state: str
    decision_log_path: Path
    run_dir: Path
    evidence: list[dict[str, Any]] = field(default_factory=list)


def run(
    request: RunRequest,
    agents: Sequence[AgentSpec],
    *,
    runs_root: Path,
    observed_at: str,
    run_id: str | None = None,
) -> RunResult:
    """Route, prioritise, and sequence Agents for one run.

    Unknown intent → NHV Evidence + Decision log; no Agent invented.
    Human review gates stop the run until ``resume`` records approval.
    """
    rid = run_id or str(uuid.uuid4())
    run_dir = runs_root / rid
    run_dir.mkdir(parents=True, exist_ok=True)
    decision_log_path = run_dir / "decision_log.jsonl"
    evidence_path = run_dir / "evidence.jsonl"

    schedule = _build_schedule(request, agents)
    if not schedule:
        evidence_id = f"{rid}-routing-nhv"
        evidence = {
            **nhv_evidence(
                pack="orchestrator",
                tool="routing",
                verification_reason="empty_result",
                claim=(
                    f"Unknown or unmatched intent {request.intent!r}; "
                    "ask a human — no Agent invented"
                ),
                observed_at=observed_at,
            ),
            "id": evidence_id,
        }
        _append_jsonl(evidence_path, evidence)
        _append_decision(
            decision_log_path,
            {
                "decision_id": f"{rid}-route",
                "actor": "orchestrator",
                "timestamp": observed_at,
                "kind": "routing",
                "inputs": {
                    "goal": request.goal,
                    "intent": request.intent,
                    "primary_outcome": request.primary_outcome,
                    "reach": request.reach,
                    "playbook": request.playbook,
                    "property_refs": dict(request.property_refs),
                },
                "skills": [],
                "agents": [],
                "outcome": "ask_human",
                "evidence_ids": [evidence_id],
                "human_review": "awaiting_approval",
                "rationale": "Unknown or unmatched intent; ask human / NHV",
            },
        )
        _write_state(
            run_dir,
            {
                "request": _request_dict(request),
                "schedule": [],
                "next_index": 0,
                "gate_state": "closed",
                "agent_statuses": [],
                "evidence_refs": [evidence_id],
            },
        )
        return RunResult(
            run_id=rid,
            agent_statuses=[],
            evidence_refs=[evidence_id],
            gate_state="closed",
            decision_log_path=decision_log_path,
            run_dir=run_dir,
            evidence=[evidence],
        )

    _append_decision(
        decision_log_path,
        {
            "decision_id": f"{rid}-route",
            "actor": "orchestrator",
            "timestamp": observed_at,
            "kind": "routing",
            "inputs": {
                "goal": request.goal,
                "intent": request.intent,
                "primary_outcome": request.primary_outcome,
                "reach": request.reach,
                "playbook": request.playbook,
                "property_refs": dict(request.property_refs),
            },
            "skills": [],
            "agents": [a.name for a in schedule],
            "outcome": "scheduled",
            "evidence_ids": [],
            "human_review": "not_required",
            "rationale": "Matched Agents by intent/outcome/Reach",
        },
    )

    ordered = _prioritise(schedule)
    _append_decision(
        decision_log_path,
        {
            "decision_id": f"{rid}-priority",
            "actor": "orchestrator",
            "timestamp": observed_at,
            "kind": "prioritisation",
            "inputs": {"agents": [a.name for a in schedule]},
            "skills": [],
            "agents": [a.name for a in ordered],
            "outcome": "ordered",
            "evidence_ids": [],
            "human_review": "not_required",
            "rationale": _priority_rationale(schedule),
        },
    )
    _append_decision(
        decision_log_path,
        {
            "decision_id": f"{rid}-schedule",
            "actor": "orchestrator",
            "timestamp": observed_at,
            "kind": "schedule",
            "inputs": {"playbook": request.playbook},
            "skills": [],
            "agents": [a.name for a in ordered],
            "outcome": "sequential",
            "evidence_ids": [],
            "human_review": "not_required",
            "rationale": "Sequential multi-agent default on shared Run directory",
        },
    )

    agent_by_name = {a.name: a for a in agents}
    return _execute_from(
        run_id=rid,
        run_dir=run_dir,
        decision_log_path=decision_log_path,
        evidence_path=evidence_path,
        request=request,
        ordered_names=[a.name for a in ordered],
        agent_by_name=agent_by_name,
        start_index=0,
        prior_statuses=[],
        prior_evidence_refs=[],
        prior_evidence=[],
        observed_at=observed_at,
    )


def resume(
    run_id: str,
    agents: Sequence[AgentSpec],
    *,
    runs_root: Path,
    approved: bool,
    observed_at: str,
) -> RunResult:
    """Resume a run stopped on a Human review gate."""
    run_dir = runs_root / run_id
    decision_log_path = run_dir / "decision_log.jsonl"
    evidence_path = run_dir / "evidence.jsonl"
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

    if state.get("gate_state") != "awaiting_approval":
        raise ValueError(f"run {run_id!r} is not awaiting Human review approval")

    paused_agent = state.get("paused_agent")
    _append_decision(
        decision_log_path,
        {
            "decision_id": f"{run_id}-gate-resume",
            "actor": "orchestrator",
            "timestamp": observed_at,
            "kind": "gate",
            "inputs": {"paused_agent": paused_agent, "approved": approved},
            "skills": [],
            "agents": [paused_agent] if paused_agent else [],
            "outcome": "approved" if approved else "rejected",
            "evidence_ids": list(state.get("evidence_refs", [])),
            "human_review": "approved" if approved else "rejected",
            "rationale": (
                "Human approved gate; Orchestrator resumes"
                if approved
                else "Human rejected gate; Orchestrator stops"
            ),
        },
    )

    if not approved:
        statuses = list(state.get("agent_statuses", []))
        _write_state(
            run_dir,
            {
                **state,
                "gate_state": "closed",
                "paused_agent": None,
            },
        )
        return RunResult(
            run_id=run_id,
            agent_statuses=statuses,
            evidence_refs=list(state.get("evidence_refs", [])),
            gate_state="closed",
            decision_log_path=decision_log_path,
            run_dir=run_dir,
            evidence=_load_evidence(evidence_path),
        )

    request = RunRequest(**state["request"])
    agent_by_name = {a.name: a for a in agents}
    # Continue from the paused agent (inclusive) now that gate is approved.
    start_index = int(state["next_index"])
    prior_statuses = [
        status
        for status in state.get("agent_statuses", [])
        if not (
            status.get("name") == paused_agent
            and status.get("status") == "awaiting_human_review"
        )
    ]
    return _execute_from(
        run_id=run_id,
        run_dir=run_dir,
        decision_log_path=decision_log_path,
        evidence_path=evidence_path,
        request=request,
        ordered_names=list(state["schedule"]),
        agent_by_name=agent_by_name,
        start_index=start_index,
        prior_statuses=prior_statuses,
        prior_evidence_refs=list(state.get("evidence_refs", [])),
        prior_evidence=_load_evidence(evidence_path),
        observed_at=observed_at,
        gate_approved_for=paused_agent,
    )


def _execute_from(
    *,
    run_id: str,
    run_dir: Path,
    decision_log_path: Path,
    evidence_path: Path,
    request: RunRequest,
    ordered_names: Sequence[str],
    agent_by_name: Mapping[str, AgentSpec],
    start_index: int,
    prior_statuses: list[dict[str, str]],
    prior_evidence_refs: list[str],
    prior_evidence: list[dict[str, Any]],
    observed_at: str,
    gate_approved_for: str | None = None,
) -> RunResult:
    statuses = list(prior_statuses)
    evidence_refs = list(prior_evidence_refs)
    evidence = list(prior_evidence)
    idx = start_index

    while idx < len(ordered_names):
        name = ordered_names[idx]
        agent = agent_by_name[name]

        if (
            agent.human_review_gate == "required"
            and gate_approved_for != name
        ):
            _append_decision(
                decision_log_path,
                {
                    "decision_id": f"{run_id}-gate-stop-{name}",
                    "actor": "orchestrator",
                    "timestamp": observed_at,
                    "kind": "gate",
                    "inputs": {"agent": name},
                    "skills": [],
                    "agents": [name],
                    "outcome": "awaiting_approval",
                    "evidence_ids": list(evidence_refs),
                    "human_review": "awaiting_approval",
                    "rationale": (
                        "Orchestrator owns the stop until Decision log approval; "
                        "gates are never skipped for cost"
                    ),
                },
            )
            statuses.append({"name": name, "status": "awaiting_human_review"})
            _write_state(
                run_dir,
                {
                    "request": _request_dict(request),
                    "schedule": list(ordered_names),
                    "next_index": idx,
                    "paused_agent": name,
                    "gate_state": "awaiting_approval",
                    "agent_statuses": statuses,
                    "evidence_refs": evidence_refs,
                },
            )
            return RunResult(
                run_id=run_id,
                agent_statuses=statuses,
                evidence_refs=evidence_refs,
                gate_state="awaiting_approval",
                decision_log_path=decision_log_path,
                run_dir=run_dir,
                evidence=evidence,
            )

        ctx = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "goal": request.goal,
            "property_refs": dict(request.property_refs),
            "primary_outcome": request.primary_outcome,
            "reach": request.reach,
        }
        outcome: Mapping[str, Any] = {"evidence_ids": [], "status": "completed"}
        if agent.execute is not None:
            outcome = agent.execute(ctx)
        ev_ids = list(outcome.get("evidence_ids") or [])
        for evidence_id in ev_ids:
            if evidence_id not in evidence_refs:
                evidence_refs.append(str(evidence_id))
        status = str(outcome.get("status") or "completed")
        statuses.append({"name": name, "status": status})

        if status == "awaiting_human_review":
            _append_decision(
                decision_log_path,
                {
                    "decision_id": f"{run_id}-gate-stop-{name}",
                    "actor": "orchestrator",
                    "timestamp": observed_at,
                    "kind": "gate",
                    "inputs": {"agent": name, "source": "agent_execute_status"},
                    "skills": [],
                    "agents": [name],
                    "outcome": "awaiting_approval",
                    "evidence_ids": list(evidence_refs),
                    "human_review": "awaiting_approval",
                    "rationale": (
                        "Agent execute returned awaiting_human_review; "
                        "Orchestrator owns the stop until Decision log approval"
                    ),
                },
            )
            _write_state(
                run_dir,
                {
                    "request": _request_dict(request),
                    "schedule": list(ordered_names),
                    "next_index": idx,
                    "paused_agent": name,
                    "gate_state": "awaiting_approval",
                    "agent_statuses": statuses,
                    "evidence_refs": evidence_refs,
                },
            )
            return RunResult(
                run_id=run_id,
                agent_statuses=statuses,
                evidence_refs=evidence_refs,
                gate_state="awaiting_approval",
                decision_log_path=decision_log_path,
                run_dir=run_dir,
                evidence=evidence,
            )

        gate_approved_for = None
        idx += 1

    _write_state(
        run_dir,
        {
            "request": _request_dict(request),
            "schedule": list(ordered_names),
            "next_index": idx,
            "paused_agent": None,
            "gate_state": "closed",
            "agent_statuses": statuses,
            "evidence_refs": evidence_refs,
        },
    )
    return RunResult(
        run_id=run_id,
        agent_statuses=statuses,
        evidence_refs=evidence_refs,
        gate_state="closed",
        decision_log_path=decision_log_path,
        run_dir=run_dir,
        evidence=evidence,
    )


def _build_schedule(
    request: RunRequest, agents: Sequence[AgentSpec]
) -> list[AgentSpec]:
    if request.playbook == "thin_audit":
        by_role = {
            a.pipeline_role: a
            for a in agents
            if a.pipeline_role is not None
        }
        scheduled: list[AgentSpec] = []
        for role in THIN_AUDIT_ORDER:
            agent = by_role.get(role)
            if agent is not None:
                scheduled.append(agent)
        return scheduled

    matched: list[AgentSpec] = []
    for agent in agents:
        if agent.primary_outcome != request.primary_outcome:
            continue
        if request.intent not in agent.when_to_use:
            continue
        if agent.reach is not None:
            if request.reach is None or request.reach not in agent.reach:
                continue
        matched.append(agent)
    return matched


def _prioritise(agents: Sequence[AgentSpec]) -> list[AgentSpec]:
    if not agents:
        return []
    if all(a.severity is not None and a.impact is not None for a in agents):
        return sorted(
            agents,
            key=lambda a: (
                -((a.severity or 0) * (a.impact or 0)),
                a.name,
            ),
        )
    return list(agents)


def _priority_rationale(agents: Sequence[AgentSpec]) -> str:
    if agents and all(
        a.severity is not None and a.impact is not None for a in agents
    ):
        return "severity×impact descending when scores exist"
    return "FIFO within the run (no complete severity×impact scores)"


def _request_dict(request: RunRequest) -> dict[str, Any]:
    return {
        "goal": request.goal,
        "intent": request.intent,
        "primary_outcome": request.primary_outcome,
        "property_refs": dict(request.property_refs),
        "reach": request.reach,
        "playbook": request.playbook,
    }


def _append_decision(path: Path, entry: Mapping[str, Any]) -> None:
    _append_jsonl(path, entry)


def _append_jsonl(path: Path, entry: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(entry), sort_keys=True) + "\n")


def _write_state(run_dir: Path, state: Mapping[str, Any]) -> None:
    (run_dir / "state.json").write_text(
        json.dumps(dict(state), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_evidence(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
