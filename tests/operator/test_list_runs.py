"""Operator bridge black-box: list Runs for sidebar rows."""

from __future__ import annotations

from pathlib import Path

from sageo.operator import list_runs, start_thin_audit_run
from sageo.orchestrator import AgentSpec


def _agents() -> list[AgentSpec]:
    def make(name: str, role: str) -> AgentSpec:
        return AgentSpec(
            name=name,
            primary_outcome="SEO",
            when_to_use=frozenset({"unused"}),
            pipeline_role=role,  # type: ignore[arg-type]
            execute=lambda _c: {"evidence_ids": [f"{name}-ev"], "status": "completed"},
        )

    return [
        make("measurement-evidence", "measurement"),
        make("technical-findings", "technical"),
        make("content-aio", "content_aio"),
    ]


def test_list_runs_empty_when_no_runs(tmp_path: Path) -> None:
    assert list_runs(tmp_path / "runs") == []


def test_list_runs_sidebar_metadata(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://www.example.com/path",
        reach="national",
        goal="National audit",
        agents=_agents(),
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-a",
    )

    rows = list_runs(runs_root)
    assert len(rows) == 1
    row = rows[0]
    assert row.run_id == "run-a"
    assert row.goal == "National audit"
    assert row.site_host == "www.example.com"
    assert row.reach == "national"
    assert row.status == "completed"


def test_list_runs_awaiting_approval_status(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    agents = [
        AgentSpec(
            name="gated",
            primary_outcome="SEO",
            when_to_use=frozenset({"unused"}),
            pipeline_role="technical",
            human_review_gate="required",
            execute=lambda _c: {"evidence_ids": ["g"], "status": "completed"},
        )
    ]
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://local.example/",
        reach="local",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-gated",
    )

    rows = list_runs(runs_root)
    assert rows[0].status == "awaiting_approval"
    assert rows[0].reach == "local"
    assert rows[0].site_host == "local.example"


def test_list_runs_most_recent_first(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    agents = _agents()
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://a.example/",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-older",
    )
    start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://b.example/",
        agents=agents,
        observed_at="2026-10-29T12:01:00+00:00",
        run_id="run-newer",
    )
    ids = [row.run_id for row in list_runs(runs_root)]
    assert ids[0] == "run-newer"
    assert set(ids) == {"run-older", "run-newer"}
