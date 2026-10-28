"""Orchestrator black-box: severity×impact prioritisation vs FIFO."""

from __future__ import annotations

from pathlib import Path

from sageo.orchestrator import AgentSpec, RunRequest, run


def _scored_agent(
    name: str,
    *,
    severity: int | None,
    impact: int | None,
    calls: list[str],
) -> AgentSpec:
    def execute(_ctx: object) -> dict:
        calls.append(name)
        return {"evidence_ids": [f"{name}-ev"], "status": "completed"}

    return AgentSpec(
        name=name,
        primary_outcome="SEO",
        when_to_use=frozenset({"audit"}),
        severity=severity,
        impact=impact,
        execute=execute,
    )


def test_fifo_when_scores_incomplete(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [
        _scored_agent("first", severity=None, impact=None, calls=calls),
        _scored_agent("second", severity=5, impact=5, calls=calls),
    ]
    run(
        RunRequest(
            goal="Audit",
            intent="audit",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-fifo",
    )
    assert calls == ["first", "second"]


def test_severity_times_impact_when_all_scored(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [
        _scored_agent("low", severity=1, impact=2, calls=calls),
        _scored_agent("high", severity=5, impact=4, calls=calls),
        _scored_agent("mid", severity=3, impact=3, calls=calls),
    ]
    result = run(
        RunRequest(
            goal="Audit",
            intent="audit",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-priority",
    )
    assert calls == ["high", "mid", "low"]
    log = result.decision_log_path.read_text(encoding="utf-8")
    assert "severity" in log
    assert "prioritisation" in log
