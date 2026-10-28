"""Orchestrator black-box: Human review gate stop and resume."""

from __future__ import annotations

import json
from pathlib import Path

from sageo.orchestrator import AgentSpec, RunRequest, resume, run


def _gate_resume_entries(path: Path) -> list[dict]:
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [
        e
        for e in entries
        if e.get("kind") == "gate" and e.get("outcome") in {"approved", "rejected"}
    ]


def _gated_agents(calls: list[str]) -> list[AgentSpec]:
    return [
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


def test_execute_awaiting_human_review_pauses_after_agent_runs(
    tmp_path: Path,
) -> None:
    """Agent-declared gates surface as execute status; Orchestrator still stops."""
    calls: list[str] = []
    agents = [
        AgentSpec(
            name="packager",
            primary_outcome="SEO",
            when_to_use=frozenset({"package"}),
            human_review_gate="not_required",
            execute=lambda _c: (
                calls.append("packager")
                or {
                    "evidence_ids": ["ev-pack"],
                    "status": "awaiting_human_review",
                }
            ),
        ),
        AgentSpec(
            name="follow-up",
            primary_outcome="SEO",
            when_to_use=frozenset({"package"}),
            human_review_gate="not_required",
            execute=lambda _c: (
                calls.append("follow-up")
                or {"evidence_ids": ["ev-follow"], "status": "completed"}
            ),
        ),
    ]

    paused = run(
        RunRequest(
            goal="Package",
            intent="package",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-agent-gate",
    )

    assert calls == ["packager"]
    assert paused.gate_state == "awaiting_approval"
    assert paused.evidence_refs == ["ev-pack"]
    assert paused.agent_statuses == [
        {"name": "packager", "status": "awaiting_human_review"},
    ]

    resumed = resume(
        "run-agent-gate",
        [
            AgentSpec(
                name="packager",
                primary_outcome="SEO",
                when_to_use=frozenset({"package"}),
                human_review_gate="not_required",
                execute=lambda _c: (
                    calls.append("packager-resume")
                    or {"evidence_ids": ["ev-pack"], "status": "completed"}
                ),
            ),
            agents[1],
        ],
        runs_root=tmp_path,
        approved=True,
        observed_at="2026-10-28T12:05:00+00:00",
    )

    assert calls == ["packager", "packager-resume", "follow-up"]
    assert resumed.gate_state == "closed"
    assert resumed.evidence_refs == ["ev-pack", "ev-follow"]
    assert resumed.agent_statuses == [
        {"name": "packager", "status": "completed"},
        {"name": "follow-up", "status": "completed"},
    ]


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


def test_resume_approve_with_operator_note_records_note_and_suffix(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    agents = _gated_agents(calls)
    run(
        RunRequest(
            goal="Remediate",
            intent="remediate",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate-note-approve",
    )

    resumed = resume(
        "run-gate-note-approve",
        agents,
        runs_root=tmp_path,
        approved=True,
        observed_at="2026-10-28T12:05:00+00:00",
        operator_note="Looks good after NAP check",
    )

    assert resumed.gate_state == "closed"
    entry = _gate_resume_entries(resumed.decision_log_path)[-1]
    assert entry["outcome"] == "approved"
    assert entry["inputs"]["operator_note"] == "Looks good after NAP check"
    assert entry["rationale"].startswith("Human approved gate; Orchestrator resumes")
    assert entry["rationale"].endswith("Looks good after NAP check")


def test_resume_reject_with_operator_note_records_note_and_suffix(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    agents = _gated_agents(calls)
    run(
        RunRequest(
            goal="Remediate",
            intent="remediate",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate-note-reject",
    )

    rejected = resume(
        "run-gate-note-reject",
        agents,
        runs_root=tmp_path,
        approved=False,
        observed_at="2026-10-28T12:05:00+00:00",
        operator_note="Need better Evidence before listing changes",
    )

    assert rejected.gate_state == "closed"
    assert calls == ["finder"]
    entry = _gate_resume_entries(rejected.decision_log_path)[-1]
    assert entry["outcome"] == "rejected"
    assert entry["inputs"]["operator_note"] == (
        "Need better Evidence before listing changes"
    )
    assert entry["rationale"].startswith("Human rejected gate; Orchestrator stops")
    assert entry["rationale"].endswith(
        "Need better Evidence before listing changes"
    )


def test_resume_omitted_or_empty_operator_note_keeps_stock_rationale(
    tmp_path: Path,
) -> None:
    cases = (
        ("run-gate-note-omit-approve", None, True),
        ("run-gate-note-empty-approve", "", True),
        ("run-gate-note-omit-reject", None, False),
        ("run-gate-note-empty-reject", "", False),
    )
    for run_id, note, approved in cases:
        calls: list[str] = []
        agents = _gated_agents(calls)
        run(
            RunRequest(
                goal="Remediate",
                intent="remediate",
                primary_outcome="SEO",
                property_refs={"site": "https://example.com/"},
            ),
            agents,
            runs_root=tmp_path,
            observed_at="2026-10-28T12:00:00+00:00",
            run_id=run_id,
        )
        kwargs: dict = {
            "runs_root": tmp_path,
            "approved": approved,
            "observed_at": "2026-10-28T12:05:00+00:00",
        }
        if note is not None:
            kwargs["operator_note"] = note
        resumed = resume(run_id, agents, **kwargs)
        entry = _gate_resume_entries(resumed.decision_log_path)[-1]
        assert entry["outcome"] == ("approved" if approved else "rejected")
        assert "operator_note" not in entry["inputs"]
        if approved:
            assert entry["rationale"] == "Human approved gate; Orchestrator resumes"
        else:
            assert entry["rationale"] == "Human rejected gate; Orchestrator stops"
