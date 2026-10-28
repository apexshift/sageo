"""Orchestrator black-box: routing by intent/outcome/Reach and unknown-intent NHV."""

from __future__ import annotations

from pathlib import Path

from sageo.orchestrator import AgentSpec, RunRequest, run


def _agent(
    name: str,
    *,
    outcome: str = "SEO",
    when: frozenset[str] | None = None,
    reach: frozenset[str] | None = None,
    gate: str = "not_required",
    calls: list[str] | None = None,
) -> AgentSpec:
    record = calls if calls is not None else []

    def execute(_ctx: object) -> dict:
        record.append(name)
        return {"evidence_ids": [f"{name}-ev-1"], "status": "completed"}

    return AgentSpec(
        name=name,
        primary_outcome=outcome,
        when_to_use=when or frozenset({name}),
        reach=reach,
        human_review_gate=gate,  # type: ignore[arg-type]
        execute=execute,
    )


def test_unknown_intent_emits_nhv_and_runs_no_agents(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [_agent("technical-placeholder", when=frozenset({"technical-audit"}), calls=calls)]
    result = run(
        RunRequest(
            goal="Do something vague",
            intent="completely-unknown-intent",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-unknown",
    )

    assert calls == []
    assert result.run_id == "run-unknown"
    assert result.agent_statuses == []
    assert result.gate_state == "closed"
    assert result.evidence_refs == ["run-unknown-routing-nhv"]
    assert len(result.evidence) == 1
    nhv = result.evidence[0]
    assert nhv["id"] == "run-unknown-routing-nhv"
    assert nhv["confidence"] == "needs_human_verification"
    assert nhv["verification_reason"] == "empty_result"
    assert nhv["source"] == "orchestrator/routing"
    assert "ask" in nhv["claim"].lower() or "human" in nhv["claim"].lower()

    log_path = result.decision_log_path
    assert log_path.is_file()
    text = log_path.read_text(encoding="utf-8")
    assert "routing" in text
    assert "orchestrator" in text
    assert "run-unknown-routing-nhv" in text
    assert "ask_human" in text


def test_routes_matching_intent_and_primary_outcome(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [
        _agent("seo-tech", outcome="SEO", when=frozenset({"indexability"}), calls=calls),
        _agent("aio-content", outcome="AIO", when=frozenset({"indexability"}), calls=calls),
    ]
    result = run(
        RunRequest(
            goal="Check indexability",
            intent="indexability",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-route",
    )

    assert calls == ["seo-tech"]
    assert [s["name"] for s in result.agent_statuses] == ["seo-tech"]
    assert result.agent_statuses[0]["status"] == "completed"
    assert result.evidence_refs == ["seo-tech-ev-1"]
    assert result.gate_state == "closed"


def test_reach_filters_agents_when_declared(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = [
        _agent(
            "local-agent",
            when=frozenset({"nap-audit"}),
            reach=frozenset({"local"}),
            calls=calls,
        ),
        _agent(
            "national-agent",
            when=frozenset({"nap-audit"}),
            reach=frozenset({"national"}),
            calls=calls,
        ),
    ]
    result = run(
        RunRequest(
            goal="NAP audit",
            intent="nap-audit",
            primary_outcome="SEO",
            property_refs={"site": "https://example.com/"},
            reach="local",
        ),
        agents,
        runs_root=tmp_path,
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-reach",
    )

    assert calls == ["local-agent"]
    assert [s["name"] for s in result.agent_statuses] == ["local-agent"]
