"""Golden path: local-reach Agent — stubs → GBP→schema→NAP order, required gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from sageo.agents import resume_agent, run_agent
from sageo.contract_lint import lint_agent_package, parse_skill_list

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = REPO_ROOT / "agents" / "local-reach"
TEST_ROOT = Path(__file__).parent
FIXTURES = TEST_ROOT / "fixtures"

DECLARED_SKILLS = [
    "gbp-profile-auditor",
    "local-schema-checker",
    "citation-consistency-checker",
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
    assert fm["name"] == "local-reach"
    assert meta["primary_outcome"] == "SEO"
    assert meta["human_review_gate"] == "required"
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
    assert "Reach=local" in body or "Reach = local" in body or "reach is local" in body.lower()
    assert "GBP" in body or "gbp" in body.lower()
    assert "NAP" in body


def test_happy_path_order_pauses_then_resumes(tmp_path: Path) -> None:
    calls: list[str] = []
    inputs = {
        "goal": "audit local Reach presence",
        "reach": "local",
        "gbp_profile": {"name": "Example Local Biz"},
        "page_captures": [{"url": "https://example.com/locations/town"}],
        "nap_sources": [{"name": "Example", "address": "1 High St", "phone": "+44"}],
    }
    expected = json.loads((FIXTURES / "happy" / "expected.json").read_text(encoding="utf-8"))

    paused = run_agent(
        AGENT_DIR,
        skill_stubs=_stub_map(calls),
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T18:00:00+00:00",
        run_id="lr-happy",
        inputs=inputs,
    )

    assert calls == expected["skills_invoked"]
    assert calls == [
        "gbp-profile-auditor",
        "local-schema-checker",
        "citation-consistency-checker",
    ]
    assert paused.skills_invoked == expected["skills_invoked"]
    assert paused.evidence_ids == expected["evidence_ids"]
    assert paused.status == "awaiting_human_review"
    assert paused.gate_state == "awaiting_approval"
    assert paused.agent_name == "local-reach"

    entries = _decision_entries(paused.decision_log_path)
    workflow = next(e for e in entries if e.get("kind") == "agent_workflow")
    assert workflow["actor"] == "agent"
    assert workflow["decision_id"]
    assert workflow["timestamp"] == "2026-10-28T18:00:00+00:00"
    assert workflow["skills"] == expected["skills_invoked"]
    assert workflow["evidence_ids"] == expected["evidence_ids"]
    assert workflow["outcome"] == "skills_completed"
    assert workflow["human_review"] == "pending"
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "awaiting_approval" for e in entries
    )

    resumed = resume_agent(
        "lr-happy",
        runs_root=tmp_path / "runs",
        approved=True,
        observed_at="2026-10-28T18:05:00+00:00",
    )
    assert resumed.status == "completed"
    assert resumed.gate_state == "closed"
    assert resumed.evidence_ids == expected["evidence_ids"]
    resume_entries = _decision_entries(resumed.decision_log_path)
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "approved" for e in resume_entries
    )


def test_gate_rejection_keeps_listing_recommendations_not_final(tmp_path: Path) -> None:
    calls: list[str] = []
    inputs = {"goal": "audit local Reach presence", "reach": "local"}
    paused = run_agent(
        AGENT_DIR,
        skill_stubs=_stub_map(calls),
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T18:00:00+00:00",
        run_id="lr-reject",
        inputs=inputs,
    )
    assert paused.status == "awaiting_human_review"
    assert calls == DECLARED_SKILLS

    rejected = resume_agent(
        "lr-reject",
        runs_root=tmp_path / "runs",
        approved=False,
        observed_at="2026-10-28T18:05:00+00:00",
    )
    assert rejected.status == "rejected"
    assert rejected.gate_state == "closed"
    entries = _decision_entries(rejected.decision_log_path)
    assert any(e.get("kind") == "gate" and e.get("outcome") == "rejected" for e in entries)
