"""Operator bridge: start thin_audit using checkout Agent packages."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from sageo.operator import (
    connector_credential_warnings,
    get_progress,
    list_runs,
    start_thin_audit_from_checkout,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_agent(
    agents_root: Path,
    *,
    name: str,
    human_review_gate: str = "not_required",
) -> None:
    agent_dir = agents_root / name
    agent_dir.mkdir(parents=True)
    frontmatter = {
        "name": name,
        "description": f"{name} fixture",
        "metadata": {
            "version": "0.1.0",
            "primary_outcome": "SEO",
            "skills": "alpha-skill",
            "human_review_gate": human_review_gate,
            "cost_model": "tokens_only",
        },
    }
    fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    (agent_dir / "AGENT.md").write_text(
        f"---\n{fm}\n---\n\n## Purpose\n\nFixture.\n",
        encoding="utf-8",
    )


def _checkout_with_thin_audit_agents(root: Path) -> Path:
    checkout = root / "checkout"
    (checkout / "orchestrator").mkdir(parents=True)
    agents = checkout / "agents"
    _write_agent(agents, name="technical-findings")
    _write_agent(agents, name="content-aio", human_review_gate="required")
    _write_agent(agents, name="local-reach", human_review_gate="required")
    _write_agent(agents, name="measurement-evidence", human_review_gate="required")
    return checkout


def test_start_from_checkout_national_schedule_and_sidebar(tmp_path: Path) -> None:
    checkout = _checkout_with_thin_audit_agents(tmp_path)
    runs_root = tmp_path / "runs"
    result = start_thin_audit_from_checkout(
        checkout_root=checkout,
        runs_root=runs_root,
        site_url="https://www.example.com/",
        reach="national",
        goal="National audit",
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-national",
    )
    assert result.run_id == "run-national"
    assert result.warnings == ()
    state = json.loads(
        (result.run_dir / "state.json").read_text(encoding="utf-8")
    )
    assert state["schedule"] == [
        "technical-findings",
        "content-aio",
        "measurement-evidence",
    ]
    assert "local-reach" not in state["schedule"]
    # content-aio requires Human review → Progress paused for Review CTA
    assert result.gate_state == "awaiting_approval"
    progress = get_progress(runs_root, "run-national")
    assert progress.paused_agent == "content-aio"
    assert [a.name for a in progress.agents] == state["schedule"]
    rows = list_runs(runs_root)
    assert rows[0].run_id == "run-national"
    assert rows[0].goal == "National audit"
    assert rows[0].site_host == "www.example.com"
    assert rows[0].reach == "national"
    assert rows[0].status == "awaiting_approval"


def test_start_from_checkout_local_includes_local_reach(tmp_path: Path) -> None:
    checkout = _checkout_with_thin_audit_agents(tmp_path)
    result = start_thin_audit_from_checkout(
        checkout_root=checkout,
        runs_root=tmp_path / "runs",
        site_url="https://local.example/",
        reach="local",
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-local",
    )
    state = json.loads(
        (result.run_dir / "state.json").read_text(encoding="utf-8")
    )
    assert state["schedule"] == [
        "technical-findings",
        "content-aio",
        "local-reach",
        "measurement-evidence",
    ]
    progress = get_progress(tmp_path / "runs", "run-local")
    assert [a.name for a in progress.agents] == state["schedule"]


def test_start_from_checkout_returns_credential_warnings(
    tmp_path: Path, monkeypatch
) -> None:
    checkout = _checkout_with_thin_audit_agents(tmp_path)
    monkeypatch.delenv("GSC_CLIENT_EMAIL", raising=False)
    monkeypatch.delenv("GSC_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GSC_PROPERTY_URL", raising=False)
    result = start_thin_audit_from_checkout(
        checkout_root=checkout,
        runs_root=tmp_path / "runs",
        site_url="https://example.com/",
        gsc_property="sc-domain:example.com",
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-warn",
    )
    assert result.run_dir.is_dir()
    assert result.warnings
    assert any("GSC" in w for w in result.warnings)
    # Still started (warn-and-allow).
    assert connector_credential_warnings(
        gsc_property="sc-domain:example.com",
        ga4_property=None,
        env={},
    )


def test_start_from_checkout_uses_repo_agents_when_present(tmp_path: Path) -> None:
    """Smoke against the real checkout roster mapping (no live Skills)."""
    agents_root = REPO_ROOT / "agents"
    assert (agents_root / "technical-findings" / "AGENT.md").is_file()
    result = start_thin_audit_from_checkout(
        checkout_root=REPO_ROOT,
        runs_root=tmp_path / "runs",
        site_url="https://example.com/",
        reach="local",
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-repo-local",
    )
    state = json.loads(
        (result.run_dir / "state.json").read_text(encoding="utf-8")
    )
    assert state["schedule"][0] == "technical-findings"
    assert "local-reach" in state["schedule"]
    assert state["schedule"][-1] == "measurement-evidence"
