"""Orchestrator black-box: thin audit pipeline on one shared Run directory."""

from __future__ import annotations

from pathlib import Path

from sageo.orchestrator import AgentSpec, RunRequest, run


def _thin_audit_agents(calls: list[str], *, run_id: str) -> list[AgentSpec]:
    def make(name: str, role: str) -> AgentSpec:
        def execute(ctx: dict) -> dict:
            calls.append(name)
            assert Path(ctx["run_dir"]).name == run_id
            assert (Path(ctx["run_dir"]) / "decision_log.jsonl").is_file()
            return {"evidence_ids": [f"{name}-ev"], "status": "completed"}

        return AgentSpec(
            name=name,
            primary_outcome="SEO",
            when_to_use=frozenset({"unused"}),
            pipeline_role=role,  # type: ignore[arg-type]
            execute=execute,
        )

    return [
        make("measurement-placeholder", "measurement"),
        make("local-reach-placeholder", "local_reach"),
        make("technical-placeholder", "technical"),
        make("content-aio-placeholder", "content_aio"),
    ]


def test_thin_audit_runs_technical_content_measurement_sequentially(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    agents = _thin_audit_agents(calls, run_id="run-thin-audit")

    result = run(
        RunRequest(
            goal="National thin audit",
            intent="unused",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
            playbook="thin_audit",
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-thin-audit",
    )

    assert calls == [
        "technical-placeholder",
        "content-aio-placeholder",
        "measurement-placeholder",
    ]
    assert result.gate_state == "closed"
    assert result.evidence_refs == [
        "technical-placeholder-ev",
        "content-aio-placeholder-ev",
        "measurement-placeholder-ev",
    ]
    assert (result.run_dir / "decision_log.jsonl").is_file()
    assert (tmp_path / "run-thin-audit" / "decision_log.jsonl").is_file()
    log = result.decision_log_path.read_text(encoding="utf-8")
    assert "schedule" in log
    assert "sequential" in log


def test_thin_audit_reach_local_includes_local_reach_after_content_aio(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    agents = _thin_audit_agents(calls, run_id="run-thin-audit-local")

    result = run(
        RunRequest(
            goal="Local thin audit",
            intent="unused",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
            reach="local",
            playbook="thin_audit",
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-thin-audit-local",
    )

    assert calls == [
        "technical-placeholder",
        "content-aio-placeholder",
        "local-reach-placeholder",
        "measurement-placeholder",
    ]
    assert result.gate_state == "closed"
    assert result.evidence_refs == [
        "technical-placeholder-ev",
        "content-aio-placeholder-ev",
        "local-reach-placeholder-ev",
        "measurement-placeholder-ev",
    ]
    assert [s["name"] for s in result.agent_statuses] == [
        "technical-placeholder",
        "content-aio-placeholder",
        "local-reach-placeholder",
        "measurement-placeholder",
    ]


def test_thin_audit_reach_national_omits_local_reach(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = _thin_audit_agents(calls, run_id="run-thin-audit-national")

    result = run(
        RunRequest(
            goal="National thin audit",
            intent="unused",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
            reach="national",
            playbook="thin_audit",
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-thin-audit-national",
    )

    assert calls == [
        "technical-placeholder",
        "content-aio-placeholder",
        "measurement-placeholder",
    ]
    assert "local-reach-placeholder" not in calls
    assert [s["name"] for s in result.agent_statuses] == [
        "technical-placeholder",
        "content-aio-placeholder",
        "measurement-placeholder",
    ]


def test_thin_audit_reach_global_omits_local_reach(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = _thin_audit_agents(calls, run_id="run-thin-audit-global")

    result = run(
        RunRequest(
            goal="Global thin audit",
            intent="unused",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
            reach="global",
            playbook="thin_audit",
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-thin-audit-global",
    )

    assert calls == [
        "technical-placeholder",
        "content-aio-placeholder",
        "measurement-placeholder",
    ]
    assert "local-reach-placeholder" not in calls
    assert [s["name"] for s in result.agent_statuses] == [
        "technical-placeholder",
        "content-aio-placeholder",
        "measurement-placeholder",
    ]
