"""Black-box Agent workflow seam.

``run_agent`` / ``resume_agent`` are the public interface. Skills are injected
as stubs so Agent goldens stay hermetic (no live Skill scripts or network).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

from sageo.contract_lint import parse_skill_list

SkillStub = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass
class AgentRunResult:
    """Observable outcome of one Agent workflow run or resume."""

    run_id: str
    agent_name: str
    skills_invoked: list[str]
    evidence_ids: list[str]
    gate_state: str
    status: str
    decision_log_path: Path
    run_dir: Path
    evidence: list[dict[str, Any]] = field(default_factory=list)


def run_agent(
    agent_dir: Path,
    *,
    skill_stubs: Mapping[str, SkillStub],
    runs_root: Path,
    observed_at: str,
    run_id: str | None = None,
    inputs: Mapping[str, Any] | None = None,
    skill_names: Sequence[str] | None = None,
) -> AgentRunResult:
    """Run one Agent workflow with injectable Skill stubs.

    Skills run in ``AGENT.md`` metadata order. When ``skill_names`` is omitted,
    an optional ``scripts/select_skills.py`` ``select_skills(declared, inputs)``
    may narrow the list (still in declared order). An explicit ``skill_names``
    override wins. When ``human_review_gate: required``, the run pauses after
    Skills until ``resume_agent`` records a decision.
    """
    agent_md = agent_dir / "AGENT.md"
    if not agent_md.is_file():
        raise FileNotFoundError(f"AGENT.md is required under {agent_dir}")

    frontmatter = _load_frontmatter(agent_md)
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"AGENT.md metadata must be a mapping: {agent_md}")

    agent_name = str(frontmatter.get("name") or agent_dir.name)
    declared = parse_skill_list(metadata.get("skills"))
    if not declared:
        raise ValueError(f"AGENT.md metadata.skills must list at least one Skill: {agent_md}")

    resolved_inputs = dict(inputs or {})
    if skill_names is None:
        selector = _load_skill_selector(agent_dir)
        if selector is not None:
            skill_names = selector(declared, resolved_inputs)
    ordered = _resolve_skill_order(declared, skill_names)
    gate = metadata.get("human_review_gate")
    if gate not in ("required", "not_required"):
        raise ValueError(
            f"AGENT.md metadata.human_review_gate must be "
            f"'required' or 'not_required': {agent_md}"
        )
    rid = run_id or str(uuid.uuid4())
    run_dir = runs_root / rid
    run_dir.mkdir(parents=True, exist_ok=True)
    decision_log_path = run_dir / "decision_log.jsonl"
    evidence_path = run_dir / "evidence.jsonl"

    ctx: dict[str, Any] = {
        "run_id": rid,
        "run_dir": str(run_dir),
        "agent_name": agent_name,
        "observed_at": observed_at,
        "inputs": resolved_inputs,
    }

    evidence_ids: list[str] = []
    evidence: list[dict[str, Any]] = []
    for skill_name in ordered:
        stub = skill_stubs.get(skill_name)
        if stub is None:
            raise KeyError(f"missing skill stub for {skill_name!r}")
        outcome = stub(ctx)
        ids = list(outcome.get("evidence_ids") or [])
        evidence_ids.extend(ids)
        for item in outcome.get("evidence") or []:
            if isinstance(item, Mapping):
                evidence.append(dict(item))
                _append_jsonl(evidence_path, dict(item))

    base_inputs = {"agent": agent_name, **resolved_inputs}

    if gate == "required":
        _append_decision(
            decision_log_path,
            {
                "decision_id": f"{rid}-agent-workflow",
                "actor": "agent",
                "timestamp": observed_at,
                "kind": "agent_workflow",
                "inputs": base_inputs,
                "skills": list(ordered),
                "outcome": "skills_completed",
                "evidence_ids": list(evidence_ids),
                "human_review": "pending",
                "rationale": f"Invoked Skills in declared order for Agent {agent_name}",
            },
        )
        _append_decision(
            decision_log_path,
            {
                "decision_id": f"{rid}-gate-stop",
                "actor": "agent",
                "timestamp": observed_at,
                "kind": "gate",
                "inputs": {"agent": agent_name},
                "skills": list(ordered),
                "outcome": "awaiting_approval",
                "evidence_ids": list(evidence_ids),
                "human_review": "awaiting_approval",
                "rationale": (
                    "Agent declares human_review_gate: required; "
                    "pause until Human approval before outputs are final"
                ),
            },
        )
        _write_state(
            run_dir,
            {
                "agent_name": agent_name,
                "agent_dir": str(agent_dir.resolve()),
                "skills_invoked": list(ordered),
                "evidence_ids": list(evidence_ids),
                "gate_state": "awaiting_approval",
                "status": "awaiting_human_review",
                "inputs": resolved_inputs,
                "human_review_gate": gate,
            },
        )
        return AgentRunResult(
            run_id=rid,
            agent_name=agent_name,
            skills_invoked=list(ordered),
            evidence_ids=list(evidence_ids),
            gate_state="awaiting_approval",
            status="awaiting_human_review",
            decision_log_path=decision_log_path,
            run_dir=run_dir,
            evidence=evidence,
        )

    _append_decision(
        decision_log_path,
        {
            "decision_id": f"{rid}-agent-workflow",
            "actor": "agent",
            "timestamp": observed_at,
            "kind": "agent_workflow",
            "inputs": base_inputs,
            "skills": list(ordered),
            "outcome": "completed",
            "evidence_ids": list(evidence_ids),
            "human_review": "not_required",
            "rationale": f"Agent {agent_name} completed without required Human review gate",
        },
    )
    _write_state(
        run_dir,
        {
            "agent_name": agent_name,
            "agent_dir": str(agent_dir.resolve()),
            "skills_invoked": list(ordered),
            "evidence_ids": list(evidence_ids),
            "gate_state": "closed",
            "status": "completed",
            "inputs": resolved_inputs,
            "human_review_gate": gate,
        },
    )
    return AgentRunResult(
        run_id=rid,
        agent_name=agent_name,
        skills_invoked=list(ordered),
        evidence_ids=list(evidence_ids),
        gate_state="closed",
        status="completed",
        decision_log_path=decision_log_path,
        run_dir=run_dir,
        evidence=evidence,
    )


def resume_agent(
    run_id: str,
    *,
    runs_root: Path,
    approved: bool,
    observed_at: str,
    operator_note: str | None = None,
) -> AgentRunResult:
    """Resume an Agent run paused on a required Human review gate."""
    run_dir = runs_root / run_id
    decision_log_path = run_dir / "decision_log.jsonl"
    evidence_path = run_dir / "evidence.jsonl"
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    if state.get("gate_state") != "awaiting_approval":
        raise ValueError(f"run {run_id!r} is not awaiting Human review approval")

    agent_name = str(state.get("agent_name") or "agent")
    skills_invoked = list(state.get("skills_invoked") or [])
    evidence_ids = list(state.get("evidence_ids") or [])
    evidence = _load_evidence(evidence_path)

    outcome = "approved" if approved else "rejected"
    status = "completed" if approved else "rejected"
    note = _normalized_operator_note(operator_note)
    inputs: dict[str, Any] = {"approved": approved, "agent": agent_name}
    rationale = (
        "Human approved gate; Agent outputs are final"
        if approved
        else "Human rejected gate; Agent outputs are not final"
    )
    if note is not None:
        inputs["operator_note"] = note
        rationale = f"{rationale} — {note}"
    _append_decision(
        decision_log_path,
        {
            "decision_id": f"{run_id}-gate-resume",
            "actor": "agent",
            "timestamp": observed_at,
            "kind": "gate",
            "inputs": inputs,
            "skills": skills_invoked,
            "outcome": outcome,
            "evidence_ids": evidence_ids,
            "human_review": outcome,
            "rationale": rationale,
        },
    )
    _write_state(
        run_dir,
        {
            **state,
            "gate_state": "closed",
            "status": status,
        },
    )
    return AgentRunResult(
        run_id=run_id,
        agent_name=agent_name,
        skills_invoked=skills_invoked,
        evidence_ids=evidence_ids,
        gate_state="closed",
        status=status,
        decision_log_path=decision_log_path,
        run_dir=run_dir,
        evidence=evidence,
    )


def _normalized_operator_note(operator_note: str | None) -> str | None:
    """Return a non-empty note, or None when omitted/blank."""
    if operator_note is None:
        return None
    stripped = operator_note.strip()
    return stripped or None


def _resolve_skill_order(
    declared: Sequence[str],
    skill_names: Sequence[str] | None,
) -> list[str]:
    """Return Skills to run in declared order; optional subset must be declared."""
    if skill_names is None:
        return list(declared)
    requested = list(skill_names)
    declared_set = set(declared)
    unknown = [name for name in requested if name not in declared_set]
    if unknown:
        raise ValueError(
            f"skill_names includes Skills not declared on AGENT.md: {unknown}"
        )
    requested_set = set(requested)
    return [name for name in declared if name in requested_set]


def _load_skill_selector(
    agent_dir: Path,
) -> Callable[[Sequence[str], Mapping[str, Any]], Sequence[str]] | None:
    """Load optional ``scripts/select_skills.py`` ``select_skills`` if present."""
    import importlib.util

    script_path = agent_dir / "scripts" / "select_skills.py"
    if not script_path.is_file():
        return None
    module_name = f"sageo_agent_select_skills_{agent_dir.name}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load skill selector: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    selector = getattr(module, "select_skills", None)
    if not callable(selector):
        raise ValueError(f"select_skills(declared, inputs) is required in {script_path}")
    return selector  # type: ignore[return-value]


def _load_frontmatter(agent_md: Path) -> dict[str, Any]:
    text = agent_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"AGENT.md YAML frontmatter is required: {agent_md}")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise ValueError(f"AGENT.md YAML frontmatter is required: {agent_md}")
    data = yaml.safe_load(rest[:end])
    if not isinstance(data, dict):
        raise ValueError(f"AGENT.md frontmatter must be a mapping: {agent_md}")
    return data


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _append_decision(path: Path, row: Mapping[str, Any]) -> None:
    _append_jsonl(path, row)


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
