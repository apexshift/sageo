"""Orchestrator black-box: thin audit pipeline on one shared Run directory."""

from __future__ import annotations

from pathlib import Path

from sageo.orchestrator import AgentSpec, RunRequest, run


def test_thin_audit_runs_technical_content_measurement_sequentially(
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    def make(name: str, role: str) -> AgentSpec:
        def execute(ctx: dict) -> dict:
            calls.append(name)
            # Shared Run directory for all placeholders.
            assert Path(ctx["run_dir"]).name == "run-thin-audit"
            assert (Path(ctx["run_dir"]) / "decision_log.jsonl").is_file()
            return {"evidence_ids": [f"{name}-ev"], "status": "completed"}

        return AgentSpec(
            name=name,
            primary_outcome="SEO",
            when_to_use=frozenset({"unused"}),
            pipeline_role=role,  # type: ignore[arg-type]
            execute=execute,
        )

    agents = [
        make("measurement-placeholder", "measurement"),
        make("technical-placeholder", "technical"),
        make("content-aio-placeholder", "content_aio"),
    ]

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
