"""Golden path: technical-findings Agent — stubbed Skills → order, Decision log, no gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest
import yaml

from sageo.agents import run_agent
from sageo.contract_lint import lint_agent_package, parse_skill_list

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = REPO_ROOT / "agents" / "technical-findings"
TEST_ROOT = Path(__file__).parent
FIXTURES = TEST_ROOT / "fixtures"

DECLARED_SKILLS = [
    "crawl-issue-extractor",
    "indexability-checker",
    "schema-validator",
    "cwv-scorer",
]


def _decision_entries(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _stub_map(calls: list[str]) -> dict[str, Any]:
    def make(name: str):
        def _stub(ctx: Mapping[str, Any]) -> dict[str, Any]:
            calls.append(name)
            evidence_id = f"ev-{name}"
            return {
                "evidence_ids": [evidence_id],
                "evidence": [
                    {
                        "id": evidence_id,
                        "claim": f"{name} stub finding",
                        "source": f"stub:{name}",
                        "observed_at": ctx["observed_at"],
                        "confidence": "high",
                    }
                ],
            }

        return _stub

    return {name: make(name) for name in DECLARED_SKILLS}


def test_agent_package_passes_contract_lint() -> None:
    assert AGENT_DIR.is_dir()
    assert lint_agent_package(AGENT_DIR) == []


def test_agent_metadata_matches_locked_contract() -> None:
    text = (AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    rest = text[3:]
    end = rest.find("\n---")
    assert end > 0
    fm = yaml.safe_load(rest[:end])
    meta = fm["metadata"]
    assert fm["name"] == "technical-findings"
    assert meta["primary_outcome"] == "SEO"
    assert meta["human_review_gate"] == "not_required"
    assert meta["cost_model"] == "tokens_and_connector_calls"
    assert parse_skill_list(meta["skills"]) == DECLARED_SKILLS
    body = rest[end + 4 :]
    for section in (
        "## Purpose",
        "## When to use",
        "## Inputs",
        "## Outputs",
        "## Skills invoked",
        "## Evidence",
        "## Human review points",
        "## Cost",
        "## Procedure / workflow",
    ):
        assert section in body


def test_happy_path_invokes_all_skills_without_gate_pause(tmp_path: Path) -> None:
    calls: list[str] = []
    inputs = {
        "goal": "diagnose technical blockers",
        "lab_metrics": {"lcp_ms": 2500, "cls": 0.05, "inp_ms": 180},
    }
    expected = json.loads((FIXTURES / "happy" / "expected.json").read_text(encoding="utf-8"))

    result = run_agent(
        AGENT_DIR,
        skill_stubs=_stub_map(calls),
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T15:00:00+00:00",
        run_id="tf-happy",
        inputs=inputs,
    )

    assert calls == expected["skills_invoked"]
    assert result.skills_invoked == expected["skills_invoked"]
    assert result.evidence_ids == expected["evidence_ids"]
    assert result.status == "completed"
    assert result.gate_state == "closed"
    assert result.agent_name == "technical-findings"

    entries = _decision_entries(result.decision_log_path)
    workflow = next(e for e in entries if e.get("kind") == "agent_workflow")
    assert workflow["actor"] == "agent"
    assert workflow["skills"] == expected["skills_invoked"]
    assert workflow["evidence_ids"] == expected["evidence_ids"]
    assert workflow["outcome"] == "completed"
    assert workflow["human_review"] == "not_required"
    assert "awaiting_approval" not in result.decision_log_path.read_text(encoding="utf-8")


def test_skips_cwv_when_lab_metrics_absent(tmp_path: Path) -> None:
    calls: list[str] = []
    inputs = {"goal": "diagnose technical blockers"}
    expected = json.loads(
        (FIXTURES / "no-lab-metrics" / "expected.json").read_text(encoding="utf-8")
    )

    result = run_agent(
        AGENT_DIR,
        skill_stubs=_stub_map(calls),
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T15:00:00+00:00",
        run_id="tf-no-cwv",
        inputs=inputs,
    )

    assert calls == expected["skills_invoked"]
    assert "cwv-scorer" not in result.skills_invoked
    assert result.skills_invoked == expected["skills_invoked"]
    assert result.evidence_ids == expected["evidence_ids"]
    assert result.status == "completed"
    assert result.gate_state == "closed"

    entries = _decision_entries(result.decision_log_path)
    workflow = next(e for e in entries if e.get("kind") == "agent_workflow")
    assert workflow["actor"] == "agent"
    assert workflow["skills"] == expected["skills_invoked"]
    assert workflow["evidence_ids"] == expected["evidence_ids"]
    assert workflow["outcome"] == "completed"
    assert workflow["human_review"] == "not_required"
