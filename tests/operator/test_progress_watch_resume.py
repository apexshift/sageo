"""Operator bridge black-box: Progress snapshot, watch, and gate resume."""

from __future__ import annotations

import json
from pathlib import Path

from sageo.operator import (
    get_progress,
    list_runs,
    resume_run,
    start_thin_audit_run,
    watch_run_progress,
)
from sageo.orchestrator import AgentSpec


def _completed(name: str, role: str) -> AgentSpec:
    return AgentSpec(
        name=name,
        primary_outcome="SEO",
        when_to_use=frozenset({"unused"}),
        pipeline_role=role,  # type: ignore[arg-type]
        execute=lambda _c: {"evidence_ids": [f"{name}-ev"], "status": "completed"},
    )


def _gated_pipeline() -> list[AgentSpec]:
    return [
        _completed("measurement-evidence", "measurement"),
        AgentSpec(
            name="content-aio",
            primary_outcome="SEO",
            when_to_use=frozenset({"unused"}),
            pipeline_role="content_aio",
            human_review_gate="required",
            execute=lambda _c: {
                "evidence_ids": ["content-ev"],
                "status": "completed",
            },
        ),
        _completed("technical-findings", "technical"),
    ]


def _gate_resume_entry(path: Path) -> dict:
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    resumes = [
        e
        for e in entries
        if e.get("kind") == "gate" and e.get("outcome") in {"approved", "rejected"}
    ]
    return resumes[-1]


def test_list_progress_gate_resume_flow(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    agents = _gated_pipeline()
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://flow.example/",
        reach="national",
        goal="Flow audit",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-flow",
    )

    rows = list_runs(runs_root)
    assert rows[0].run_id == "run-flow"
    assert rows[0].status == "awaiting_approval"
    assert rows[0].site_host == "flow.example"

    paused = get_progress(runs_root, "run-flow")
    assert paused.gate_state == "awaiting_approval"
    assert paused.paused_agent == "content-aio"

    resume_run(
        runs_root,
        "run-flow",
        agents=agents,
        approved=True,
        observed_at="2026-10-29T12:05:00+00:00",
        operator_note="Ship it",
    )
    done = get_progress(runs_root, "run-flow")
    assert done.gate_state == "closed"
    assert done.paused_agent is None
    assert list_runs(runs_root)[0].status == "completed"
    entry = _gate_resume_entry(runs_root / "run-flow" / "decision_log.jsonl")
    assert entry["inputs"]["operator_note"] == "Ship it"


def test_get_progress_ordered_checklist_and_paused_agent(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://example.com/",
        agents=_gated_pipeline(),
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-progress",
    )

    snap = get_progress(runs_root, "run-progress")
    assert snap.run_id == "run-progress"
    assert snap.gate_state == "awaiting_approval"
    assert snap.paused_agent == "content-aio"
    assert [a.name for a in snap.agents] == [
        "technical-findings",
        "content-aio",
        "measurement-evidence",
    ]
    assert [a.status for a in snap.agents] == [
        "completed",
        "awaiting_human_review",
        "pending",
    ]


def test_get_progress_empty_schedule_is_honest(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "run-empty"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "request": {
                    "goal": "unknown",
                    "intent": "nope",
                    "primary_outcome": "SEO",
                    "property_refs": {"site_url": "https://example.com/"},
                    "reach": "national",
                    "playbook": None,
                },
                "schedule": [],
                "next_index": 0,
                "gate_state": "closed",
                "paused_agent": None,
                "agent_statuses": [],
                "evidence_refs": ["nhv"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    snap = get_progress(runs_root, "run-empty")
    assert snap.gate_state == "closed"
    assert snap.paused_agent is None
    assert snap.agents == ()
    assert snap.empty_schedule is True


def test_resume_approve_with_operator_note(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    agents = _gated_pipeline()
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://example.com/",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-resume-approve",
    )

    result = resume_run(
        runs_root,
        "run-resume-approve",
        agents=agents,
        approved=True,
        observed_at="2026-10-29T12:05:00+00:00",
        operator_note="Looks good",
    )
    assert result.gate_state == "closed"
    entry = _gate_resume_entry(result.decision_log_path)
    assert entry["outcome"] == "approved"
    assert entry["inputs"]["operator_note"] == "Looks good"
    assert entry["rationale"].endswith("Looks good")

    snap = get_progress(runs_root, "run-resume-approve")
    assert snap.gate_state == "closed"
    assert snap.paused_agent is None
    assert [a.status for a in snap.agents] == [
        "completed",
        "completed",
        "completed",
    ]


def test_resume_reject_with_operator_note(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    agents = _gated_pipeline()
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://example.com/",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-resume-reject",
    )

    result = resume_run(
        runs_root,
        "run-resume-reject",
        agents=agents,
        approved=False,
        observed_at="2026-10-29T12:05:00+00:00",
        operator_note="Need more Evidence",
    )
    assert result.gate_state == "closed"
    entry = _gate_resume_entry(result.decision_log_path)
    assert entry["outcome"] == "rejected"
    assert entry["inputs"]["operator_note"] == "Need more Evidence"
    assert entry["rationale"].endswith("Need more Evidence")

    snap = get_progress(runs_root, "run-resume-reject")
    assert snap.gate_state == "closed"
    assert snap.agents[1].status == "awaiting_human_review"
    assert snap.agents[2].status == "pending"


def test_watch_run_progress_yields_updates_and_stops_when_idle(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    agents = _gated_pipeline()
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://example.com/",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-watch",
    )

    resumed = {"done": False}

    def sleep(_seconds: float) -> None:
        if not resumed["done"]:
            resumed["done"] = True
            resume_run(
                runs_root,
                "run-watch",
                agents=agents,
                approved=True,
                observed_at="2026-10-29T12:05:00+00:00",
            )

    snapshots = list(
        watch_run_progress(
            runs_root,
            "run-watch",
            poll_interval=0.0,
            sleep=sleep,
        )
    )
    assert snapshots[0].gate_state == "awaiting_approval"
    assert snapshots[0].paused_agent == "content-aio"
    assert snapshots[-1].gate_state == "closed"
    assert snapshots[-1].paused_agent is None
    assert any(s.gate_state == "awaiting_approval" for s in snapshots)
    assert snapshots[-1].agents[-1].status == "completed"


def test_watch_run_progress_stops_immediately_when_already_idle(
    tmp_path: Path,
) -> None:
    runs_root = tmp_path / "runs"
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://example.com/",
        agents=[
            _completed("technical-findings", "technical"),
            _completed("content-aio", "content_aio"),
            _completed("measurement-evidence", "measurement"),
        ],
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-idle",
    )
    sleeps: list[float] = []
    snapshots = list(
        watch_run_progress(
            runs_root,
            "run-idle",
            poll_interval=1.0,
            sleep=sleeps.append,
        )
    )
    assert len(snapshots) == 1
    assert snapshots[0].gate_state == "closed"
    assert sleeps == []
