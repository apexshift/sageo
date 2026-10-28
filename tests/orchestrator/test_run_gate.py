"""Orchestrator black-box: Human review gate stop and resume."""

from __future__ import annotations

from pathlib import Path

from sageo.orchestrator import AgentSpec, RunRequest, resume, run


def test_required_gate_stops_before_agent_runs(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [
        AgentSpec(
            name="finder",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="not_required",
            execute=lambda _c: (calls.append("finder") or {"evidence_ids": ["f"], "status": "completed"}),
        ),
        AgentSpec(
            name="remediator",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="required",
            execute=lambda _c: (calls.append("remediator") or {"evidence_ids": ["r"], "status": "completed"}),
        ),
        AgentSpec(
            name="publisher",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="not_required",
            execute=lambda _c: (calls.append("publisher") or {"evidence_ids": ["p"], "status": "completed"}),
        ),
    ]

    result = run(
        RunRequest(
            goal="Remediate",
            intent="remediate",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate",
    )

    assert calls == ["finder"]
    assert result.gate_state == "awaiting_approval"
    assert result.agent_statuses == [
        {"name": "finder", "status": "completed"},
        {"name": "remediator", "status": "awaiting_human_review"},
    ]
    log = result.decision_log_path.read_text(encoding="utf-8")
    assert "awaiting_approval" in log
    assert "gate" in log


def test_resume_with_approval_continues_past_gate(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [
        AgentSpec(
            name="finder",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="not_required",
            execute=lambda _c: (calls.append("finder") or {"evidence_ids": ["f"], "status": "completed"}),
        ),
        AgentSpec(
            name="remediator",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="required",
            execute=lambda _c: (
                calls.append("remediator") or {"evidence_ids": ["r"], "status": "completed"}
            ),
        ),
        AgentSpec(
            name="publisher",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="not_required",
            execute=lambda _c: (
                calls.append("publisher") or {"evidence_ids": ["p"], "status": "completed"}
            ),
        ),
    ]
    request = RunRequest(
        goal="Remediate",
        intent="remediate",
        primary_outcome="SEO",
        property_refs={"site": "https://example.com/"},
    )
    paused = run(
        request,
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate-resume",
    )
    assert paused.gate_state == "awaiting_approval"

    resumed = resume(
        "run-gate-resume",
        agents,
        runs_root=tmp_path,
        approved=True,
        observed_at="2026-10-28T12:05:00+00:00",
    )

    assert calls == ["finder", "remediator", "publisher"]
    assert resumed.gate_state == "closed"
    assert [s["name"] for s in resumed.agent_statuses] == [
        "finder",
        "remediator",
        "publisher",
    ]
    assert resumed.evidence_refs == ["f", "r", "p"]
    log = resumed.decision_log_path.read_text(encoding="utf-8")
    assert "approved" in log
    # Stop/resume reconstructible from Decision log alone (audit trail).
    assert "awaiting_approval" in log
    assert log.index("awaiting_approval") < log.index("approved")


def test_resume_with_rejection_stops_without_running_gated_agent(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    agents = [
        AgentSpec(
            name="finder",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="not_required",
            execute=lambda _c: (
                calls.append("finder") or {"evidence_ids": ["f"], "status": "completed"}
            ),
        ),
        AgentSpec(
            name="remediator",
            primary_outcome="SEO",
            when_to_use=frozenset({"remediate"}),
            human_review_gate="required",
            execute=lambda _c: (
                calls.append("remediator")
                or {"evidence_ids": ["r"], "status": "completed"}
            ),
        ),
    ]
    paused = run(
        RunRequest(
            goal="Remediate",
            intent="remediate",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate-reject",
    )
    assert paused.gate_state == "awaiting_approval"

    rejected = resume(
        "run-gate-reject",
        agents,
        runs_root=tmp_path,
        approved=False,
        observed_at="2026-10-28T12:05:00+00:00",
    )

    assert calls == ["finder"]
    assert rejected.gate_state == "closed"
    assert [s["name"] for s in rejected.agent_statuses] == [
        "finder",
        "remediator",
    ]
    assert rejected.agent_statuses[1]["status"] == "awaiting_human_review"
    log = rejected.decision_log_path.read_text(encoding="utf-8")
    assert "rejected" in log
