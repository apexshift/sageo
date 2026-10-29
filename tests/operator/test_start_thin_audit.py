"""Operator bridge black-box: start thin_audit Run from New Run fields."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sageo.operator import start_thin_audit_run
from sageo.orchestrator import AgentSpec


def _thin_audit_agents(calls: list[str]) -> list[AgentSpec]:
    def make(name: str, role: str) -> AgentSpec:
        def execute(ctx: dict) -> dict:
            calls.append(name)
            return {"evidence_ids": [f"{name}-ev"], "status": "completed"}

        return AgentSpec(
            name=name,
            primary_outcome="SEO",
            when_to_use=frozenset({"unused"}),
            pipeline_role=role,  # type: ignore[arg-type]
            execute=execute,
        )

    return [
        make("measurement-evidence", "measurement"),
        make("local-reach", "local_reach"),
        make("technical-findings", "technical"),
        make("content-aio", "content_aio"),
    ]


def _state(run_dir: Path) -> dict:
    return json.loads((run_dir / "state.json").read_text(encoding="utf-8"))


def test_start_thin_audit_national_omits_local_reach(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = _thin_audit_agents(calls)
    runs_root = tmp_path / "runs"

    result = start_thin_audit_run(
        runs_root=runs_root,
        site_url="https://example.com/",
        reach="national",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-national",
    )

    assert result.run_id == "run-national"
    assert result.run_dir == runs_root / "run-national"
    assert (result.run_dir / "decision_log.jsonl").is_file()
    assert (result.run_dir / "state.json").is_file()

    state = _state(result.run_dir)
    request = state["request"]
    assert request["playbook"] == "thin_audit"
    assert request["intent"] == "thin_audit"
    assert request["primary_outcome"] == "SEO"
    assert request["reach"] == "national"
    assert request["property_refs"] == {"site_url": "https://example.com/"}
    assert request["goal"] == "thin_audit https://example.com/ (national)"
    assert state["schedule"] == [
        "technical-findings",
        "content-aio",
        "measurement-evidence",
    ]
    assert calls == [
        "technical-findings",
        "content-aio",
        "measurement-evidence",
    ]
    assert "local-reach" not in calls


def test_start_thin_audit_local_includes_local_reach(tmp_path: Path) -> None:
    calls: list[str] = []
    agents = _thin_audit_agents(calls)

    result = start_thin_audit_run(
        runs_root=tmp_path / "runs",
        site_url="https://local.example/",
        reach="local",
        goal="Audit downtown locations",
        agents=agents,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-local",
    )

    state = _state(result.run_dir)
    request = state["request"]
    assert request["reach"] == "local"
    assert request["goal"] == "Audit downtown locations"
    assert request["playbook"] == "thin_audit"
    assert request["intent"] == "thin_audit"
    assert request["primary_outcome"] == "SEO"
    assert state["schedule"] == [
        "technical-findings",
        "content-aio",
        "local-reach",
        "measurement-evidence",
    ]
    assert calls == [
        "technical-findings",
        "content-aio",
        "local-reach",
        "measurement-evidence",
    ]


def test_start_thin_audit_defaults_reach_to_national(tmp_path: Path) -> None:
    result = start_thin_audit_run(
        runs_root=tmp_path / "runs",
        site_url="https://example.com/",
        agents=_thin_audit_agents([]),
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-default-reach",
    )
    request = _state(result.run_dir)["request"]
    assert request["reach"] == "national"
    assert request["goal"] == "thin_audit https://example.com/ (national)"


def test_start_thin_audit_omits_empty_optional_property_refs(tmp_path: Path) -> None:
    result = start_thin_audit_run(
        runs_root=tmp_path / "runs",
        site_url="https://example.com/",
        gsc_property="  ",
        ga4_property="",
        agents=_thin_audit_agents([]),
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-empty-optionals",
    )
    refs = _state(result.run_dir)["request"]["property_refs"]
    assert refs == {"site_url": "https://example.com/"}
    assert "gsc_property" not in refs
    assert "ga4_property" not in refs


def test_start_thin_audit_includes_optional_property_refs_when_set(
    tmp_path: Path,
) -> None:
    result = start_thin_audit_run(
        runs_root=tmp_path / "runs",
        site_url="https://example.com/",
        gsc_property="sc-domain:example.com",
        ga4_property="properties/123",
        agents=_thin_audit_agents([]),
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-with-connectors",
    )
    refs = _state(result.run_dir)["request"]["property_refs"]
    assert refs == {
        "site_url": "https://example.com/",
        "gsc_property": "sc-domain:example.com",
        "ga4_property": "properties/123",
    }


def test_start_thin_audit_requires_site_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="site_url"):
        start_thin_audit_run(
            runs_root=tmp_path / "runs",
            site_url="  ",
            agents=_thin_audit_agents([]),
            observed_at="2026-10-29T12:00:00+00:00",
            run_id="run-missing-site",
        )
