"""National-audit e2e: Orchestrator + three Agents, stubbed Skills, metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from sageo.agents import resume_agent, run_agent
from sageo.metrics import write_run_metrics
from sageo.orchestrator import AgentSpec, RunRequest, resume, run

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = Path(__file__).parent
EXPECTED = json.loads(
    (TEST_ROOT / "expected" / "happy.json").read_text(encoding="utf-8")
)
AGENT_INPUTS: dict[str, dict[str, Any]] = json.loads(
    (TEST_ROOT / "fixtures" / "agent_inputs.json").read_text(encoding="utf-8")
)
OBSERVED_AT = "2026-10-28T18:00:00+00:00"
RESUME_AT = "2026-10-28T18:05:00+00:00"

AGENT_DIRS = {
    "technical-findings": REPO_ROOT / "agents" / "technical-findings",
    "content-aio": REPO_ROOT / "agents" / "content-aio",
    "measurement-evidence": REPO_ROOT / "agents" / "measurement-evidence",
}


def _load_agent_meta(agent_dir: Path) -> dict[str, Any]:
    text = (agent_dir / "AGENT.md").read_text(encoding="utf-8")
    rest = text[3:]
    end = rest.find("\n---")
    fm = yaml.safe_load(rest[:end])
    assert isinstance(fm, dict)
    meta = fm.get("metadata")
    assert isinstance(meta, dict)
    return meta


def _decision_entries(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _stub_map(
    skill_names: list[str],
    calls: list[str],
    *,
    white_hat_citation: bool = False,
) -> dict[str, Any]:
    def make(name: str):
        def _stub(ctx: Mapping[str, Any]) -> dict[str, Any]:
            calls.append(name)
            evidence_id = f"ev-{name}"
            claim = f"{name} stub finding"
            evidence: dict[str, Any] = {
                "id": evidence_id,
                "claim": claim,
                "source": f"stub:{name}",
                "observed_at": ctx["observed_at"],
                "confidence": "high",
            }
            if white_hat_citation and name == "citation-opportunity-identifier":
                evidence["claim"] = "White-hat citation opportunity identified (stub)."
                evidence["method"] = "white-hat-only"
            return {"evidence_ids": [evidence_id], "evidence": [evidence]}

        return _stub

    return {name: make(name) for name in skill_names}


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _merge_agent_artifacts(
    orch_run_dir: Path,
    agent_result: Any,
    *,
    include_evidence: bool,
) -> None:
    """Copy Agent artifacts into the shared Orchestrator Run directory."""
    if include_evidence:
        evidence_path = orch_run_dir / "evidence.jsonl"
        for item in agent_result.evidence:
            _append_jsonl(evidence_path, item)
    existing_decision_ids = {
        str(entry.get("decision_id"))
        for entry in _decision_entries(orch_run_dir / "decision_log.jsonl")
        if entry.get("decision_id") is not None
    }
    for entry in _decision_entries(agent_result.decision_log_path):
        decision_id = entry.get("decision_id")
        if decision_id is not None and str(decision_id) in existing_decision_ids:
            continue
        _append_jsonl(orch_run_dir / "decision_log.jsonl", entry)
        if decision_id is not None:
            existing_decision_ids.add(str(decision_id))


def _run_agent_under_orch(
    *,
    agent_name: str,
    orch_ctx: Mapping[str, Any],
    skill_calls: list[str],
    auto_approve_agent_gate: bool,
) -> dict[str, Any]:
    agent_dir = AGENT_DIRS[agent_name]
    meta = _load_agent_meta(agent_dir)
    skills = EXPECTED["skills_by_agent"][agent_name]
    stubs = _stub_map(
        skills,
        skill_calls,
        white_hat_citation=(agent_name == "content-aio"),
    )
    orch_run_dir = Path(str(orch_ctx["run_dir"]))
    agents_root = orch_run_dir / "agents"
    agent_state_path = agents_root / agent_name / "state.json"

    if agent_state_path.is_file():
        agent_state = json.loads(agent_state_path.read_text(encoding="utf-8"))
        if agent_state.get("gate_state") == "awaiting_approval":
            result = resume_agent(
                agent_name,
                runs_root=agents_root,
                approved=True,
                observed_at=RESUME_AT,
            )
            _merge_agent_artifacts(
                orch_run_dir, result, include_evidence=False
            )
            return {
                "evidence_ids": list(result.evidence_ids),
                "status": result.status,
            }

    result = run_agent(
        agent_dir,
        skill_stubs=stubs,
        runs_root=agents_root,
        observed_at=OBSERVED_AT,
        run_id=agent_name,
        inputs=AGENT_INPUTS[agent_name],
    )
    if (
        auto_approve_agent_gate
        and result.gate_state == "awaiting_approval"
        and meta.get("human_review_gate") == "required"
    ):
        result = resume_agent(
            agent_name,
            runs_root=agents_root,
            approved=True,
            observed_at=RESUME_AT,
        )
    _merge_agent_artifacts(orch_run_dir, result, include_evidence=True)
    return {
        "evidence_ids": list(result.evidence_ids),
        "status": result.status,
    }


def _national_audit_agents(skill_calls: list[str]) -> list[AgentSpec]:
    """thin_audit AgentSpecs; Measurement package gate surfaces via execute status."""

    def execute_technical(ctx: Mapping[str, Any]) -> dict[str, Any]:
        return _run_agent_under_orch(
            agent_name="technical-findings",
            orch_ctx=ctx,
            skill_calls=skill_calls,
            auto_approve_agent_gate=False,
        )

    def execute_content(ctx: Mapping[str, Any]) -> dict[str, Any]:
        # Clear content-aio's Agent gate inside execute so the e2e asserts
        # the Measurement package gate as the national-audit Human stop.
        return _run_agent_under_orch(
            agent_name="content-aio",
            orch_ctx=ctx,
            skill_calls=skill_calls,
            auto_approve_agent_gate=True,
        )

    def execute_measurement(ctx: Mapping[str, Any]) -> dict[str, Any]:
        # Do not auto-approve: Orchestrator pauses on awaiting_human_review
        # after Skills (Measurement package gate), then resume re-enters here.
        return _run_agent_under_orch(
            agent_name="measurement-evidence",
            orch_ctx=ctx,
            skill_calls=skill_calls,
            auto_approve_agent_gate=False,
        )

    return [
        AgentSpec(
            name="technical-findings",
            primary_outcome="SEO",
            when_to_use=frozenset({"national_audit"}),
            pipeline_role="technical",
            human_review_gate="not_required",
            execute=execute_technical,
        ),
        AgentSpec(
            name="content-aio",
            primary_outcome="AIO",
            when_to_use=frozenset({"national_audit"}),
            pipeline_role="content_aio",
            human_review_gate="not_required",
            execute=execute_content,
        ),
        AgentSpec(
            name="measurement-evidence",
            primary_outcome="SEO",
            when_to_use=frozenset({"national_audit"}),
            pipeline_role="measurement",
            human_review_gate="not_required",
            execute=execute_measurement,
        ),
    ]


def test_national_audit_e2e_routes_gates_skills_and_metrics(tmp_path: Path) -> None:
    skill_calls: list[str] = []
    agents = _national_audit_agents(skill_calls)
    request = RunRequest(
        goal="National audit for example.com",
        intent="national_audit",
        primary_outcome="SEO",
        property_refs={"site": "https://example.com/"},
        reach="national",
        playbook="thin_audit",
    )

    paused = run(
        request,
        agents,
        runs_root=tmp_path / "runs",
        observed_at=OBSERVED_AT,
        run_id="national-audit",
    )

    # Measurement package gate: Skills have already run; Human approval pending.
    assert skill_calls == EXPECTED["skills_invoked"]
    assert paused.gate_state == "awaiting_approval"
    assert paused.agent_statuses == [
        {"name": "technical-findings", "status": "completed"},
        {"name": "content-aio", "status": "completed"},
        {"name": "measurement-evidence", "status": "awaiting_human_review"},
    ]
    assert paused.evidence_refs == [
        f"ev-{name}" for name in EXPECTED["skills_invoked"]
    ]
    assert (paused.run_dir / "decision_log.jsonl").is_file()
    assert (paused.run_dir / "evidence.jsonl").is_file()
    orch_log = paused.decision_log_path.read_text(encoding="utf-8")
    assert "awaiting_approval" in orch_log
    assert "measurement-evidence" in orch_log
    measurement_log = (
        paused.run_dir / "agents" / "measurement-evidence" / "decision_log.jsonl"
    )
    measurement_entries = _decision_entries(measurement_log)
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "awaiting_approval"
        for e in measurement_entries
    )
    measurement_workflow = next(
        e for e in measurement_entries if e.get("kind") == "agent_workflow"
    )
    assert (
        measurement_workflow["skills"]
        == EXPECTED["skills_by_agent"]["measurement-evidence"]
    )
    assert measurement_workflow["skills"][-1] == "evidence-packager"

    completed = resume(
        "national-audit",
        agents,
        runs_root=tmp_path / "runs",
        approved=True,
        observed_at=RESUME_AT,
    )

    assert skill_calls == EXPECTED["skills_invoked"]
    assert completed.gate_state == "closed"
    assert [s["name"] for s in completed.agent_statuses] == EXPECTED["agent_order"]
    assert completed.agent_statuses == [
        {"name": "technical-findings", "status": "completed"},
        {"name": "content-aio", "status": "completed"},
        {"name": "measurement-evidence", "status": "completed"},
    ]
    assert completed.evidence_refs == [
        f"ev-{name}" for name in EXPECTED["skills_invoked"]
    ]

    # Nested Agent runs used real AGENT.md contracts (Skill order + gates).
    for agent_name, skills in EXPECTED["skills_by_agent"].items():
        agent_log = completed.run_dir / "agents" / agent_name / "decision_log.jsonl"
        assert agent_log.is_file()
        workflow = next(
            e for e in _decision_entries(agent_log) if e.get("kind") == "agent_workflow"
        )
        assert workflow["skills"] == skills

    resume_entries = _decision_entries(completed.decision_log_path)
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "approved" for e in resume_entries
    )
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "approved"
        for e in _decision_entries(measurement_log)
    )

    invocations = [
        {
            "component": "technical-findings",
            "cost_model": "tokens_and_connector_calls",
        },
        {
            "component": "content-aio",
            "cost_model": "tokens_and_connector_calls",
        },
        {
            "component": "measurement-evidence",
            "cost_model": "tokens_only",
        },
    ]
    (completed.run_dir / "invocations.json").write_text(
        json.dumps(invocations, indent=2) + "\n",
        encoding="utf-8",
    )
    report = write_run_metrics(
        completed.run_dir,
        usage={"tokens": 900, "connector_calls": 4},
    )

    assert (completed.run_dir / "metrics.json").is_file()
    assert report["evidence_completeness"]["status"] == "pass"
    assert "cost" in report
    assert report["cost"]["tokens_class"] == "from_usage_stub"
    dumped = json.dumps(report).lower()
    assert "ranking" not in dumped
    assert "traffic" not in dumped
