"""Agent workflow black box: stubbed Skills, Decision log, gate pause/resume."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from sageo.agents import resume_agent, run_agent


def _write_agent(
    root: Path,
    *,
    name: str,
    skills: str,
    human_review_gate: str,
    cost_model: str = "tokens_and_connector_calls",
    primary_outcome: str = "SEO",
) -> Path:
    agent_dir = root / name
    agent_dir.mkdir(parents=True)
    frontmatter = {
        "name": name,
        "description": f"{name} workflow for harness tests.",
        "metadata": {
            "version": "0.1.0",
            "primary_outcome": primary_outcome,
            "skills": skills,
            "human_review_gate": human_review_gate,
            "cost_model": cost_model,
        },
    }
    fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    (agent_dir / "AGENT.md").write_text(
        f"---\n{fm}\n---\n\n## Purpose\n\nHarness fixture.\n",
        encoding="utf-8",
    )
    return agent_dir


def _decision_entries(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_run_invokes_stubbed_skills_in_declared_order(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill,beta-skill",
        human_review_gate="not_required",
    )
    calls: list[str] = []

    def stub_alpha(ctx: dict) -> dict:
        calls.append("alpha-skill")
        return {
            "evidence_ids": ["ev-alpha"],
            "evidence": [
                {
                    "id": "ev-alpha",
                    "claim": "alpha finding",
                    "source": "stub:alpha",
                    "observed_at": ctx["observed_at"],
                    "confidence": "high",
                }
            ],
        }

    def stub_beta(ctx: dict) -> dict:
        calls.append("beta-skill")
        return {
            "evidence_ids": ["ev-beta"],
            "evidence": [
                {
                    "id": "ev-beta",
                    "claim": "beta finding",
                    "source": "stub:beta",
                    "observed_at": ctx["observed_at"],
                    "confidence": "medium",
                }
            ],
        }

    result = run_agent(
        agent_dir,
        skill_stubs={"alpha-skill": stub_alpha, "beta-skill": stub_beta},
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-order",
        inputs={"goal": "diagnose"},
    )

    assert calls == ["alpha-skill", "beta-skill"]
    assert result.skills_invoked == ["alpha-skill", "beta-skill"]
    assert result.evidence_ids == ["ev-alpha", "ev-beta"]
    assert result.status == "completed"
    assert result.gate_state == "closed"
    assert result.agent_name == "fixture-agent"


def test_run_writes_decision_log_with_evidence_ids(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill",
        human_review_gate="not_required",
    )

    result = run_agent(
        agent_dir,
        skill_stubs={
            "alpha-skill": lambda _ctx: {
                "evidence_ids": ["ev-1"],
                "evidence": [{"id": "ev-1", "claim": "c", "source": "s", "observed_at": "t", "confidence": "high"}],
            }
        },
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-decision",
        inputs={"goal": "diagnose"},
    )

    entries = _decision_entries(result.decision_log_path)
    assert entries, "expected at least one Decision log entry"
    workflow = next(e for e in entries if e.get("kind") == "agent_workflow")
    assert workflow["actor"] == "agent"
    assert workflow["inputs"]["agent"] == "fixture-agent"
    assert workflow["skills"] == ["alpha-skill"]
    assert workflow["evidence_ids"] == ["ev-1"]
    assert workflow["outcome"] == "completed"
    assert workflow["human_review"] == "not_required"


def test_not_required_gate_completes_without_pause(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill",
        human_review_gate="not_required",
    )
    result = run_agent(
        agent_dir,
        skill_stubs={"alpha-skill": lambda _c: {"evidence_ids": ["e"], "evidence": []}},
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-no-gate",
    )
    assert result.status == "completed"
    assert result.gate_state == "closed"
    assert "awaiting_approval" not in result.decision_log_path.read_text(encoding="utf-8")


def test_required_gate_pauses_after_skills_awaiting_human_review(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="gated-agent",
        skills="alpha-skill,beta-skill",
        human_review_gate="required",
    )
    calls: list[str] = []

    def stub(name: str, evidence_id: str):
        def _stub(ctx: dict) -> dict:
            calls.append(name)
            return {
                "evidence_ids": [evidence_id],
                "evidence": [
                    {
                        "id": evidence_id,
                        "claim": f"{name} finding",
                        "source": f"stub:{name}",
                        "observed_at": ctx["observed_at"],
                        "confidence": "high",
                    }
                ],
            }

        return _stub

    result = run_agent(
        agent_dir,
        skill_stubs={
            "alpha-skill": stub("alpha-skill", "a"),
            "beta-skill": stub("beta-skill", "b"),
        },
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate",
        inputs={"goal": "package"},
    )

    assert calls == ["alpha-skill", "beta-skill"]
    assert result.status == "awaiting_human_review"
    assert result.gate_state == "awaiting_approval"
    assert result.evidence_ids == ["a", "b"]
    entries = _decision_entries(result.decision_log_path)
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "awaiting_approval" for e in entries
    )


def test_resume_with_approval_completes_gated_agent(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="gated-agent",
        skills="alpha-skill",
        human_review_gate="required",
    )
    stubs = {
        "alpha-skill": lambda _c: {
            "evidence_ids": ["a"],
            "evidence": [{"id": "a", "claim": "c", "source": "s", "observed_at": "t", "confidence": "high"}],
        }
    }
    paused = run_agent(
        agent_dir,
        skill_stubs=stubs,
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate-resume",
    )
    assert paused.status == "awaiting_human_review"

    resumed = resume_agent(
        "run-gate-resume",
        runs_root=tmp_path / "runs",
        approved=True,
        observed_at="2026-10-28T12:05:00+00:00",
    )
    assert resumed.status == "completed"
    assert resumed.gate_state == "closed"
    assert resumed.evidence_ids == ["a"]
    entries = _decision_entries(resumed.decision_log_path)
    assert any(
        e.get("kind") == "gate" and e.get("outcome") == "approved" for e in entries
    )


def test_resume_with_rejection_closes_gate(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="gated-agent",
        skills="alpha-skill",
        human_review_gate="required",
    )
    run_agent(
        agent_dir,
        skill_stubs={"alpha-skill": lambda _c: {"evidence_ids": ["a"], "evidence": []}},
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-gate-reject",
    )
    resumed = resume_agent(
        "run-gate-reject",
        runs_root=tmp_path / "runs",
        approved=False,
        observed_at="2026-10-28T12:05:00+00:00",
    )
    assert resumed.status == "rejected"
    assert resumed.gate_state == "closed"
    entries = _decision_entries(resumed.decision_log_path)
    assert any(e.get("kind") == "gate" and e.get("outcome") == "rejected" for e in entries)


def test_missing_stub_raises(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill,beta-skill",
        human_review_gate="not_required",
    )
    with pytest.raises(KeyError, match="beta-skill"):
        run_agent(
            agent_dir,
            skill_stubs={"alpha-skill": lambda _c: {"evidence_ids": [], "evidence": []}},
            runs_root=tmp_path / "runs",
            observed_at="2026-10-28T12:00:00+00:00",
            run_id="run-missing-stub",
        )


def test_optional_select_skills_script_narrows_declared_list(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill,beta-skill,gamma-skill",
        human_review_gate="not_required",
    )
    scripts = agent_dir / "scripts"
    scripts.mkdir()
    (scripts / "select_skills.py").write_text(
        "def select_skills(declared, inputs):\n"
        "    if inputs.get('skip_beta'):\n"
        "        return [n for n in declared if n != 'beta-skill']\n"
        "    return list(declared)\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    def track(name: str):
        def _stub(_ctx: dict) -> dict:
            calls.append(name)
            return {"evidence_ids": [name], "evidence": []}

        return _stub

    result = run_agent(
        agent_dir,
        skill_stubs={
            "alpha-skill": track("alpha-skill"),
            "beta-skill": track("beta-skill"),
            "gamma-skill": track("gamma-skill"),
        },
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-select-skills",
        inputs={"skip_beta": True},
    )
    assert calls == ["alpha-skill", "gamma-skill"]
    assert result.skills_invoked == ["alpha-skill", "gamma-skill"]


def test_skill_names_rejects_undeclared_skills(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill,beta-skill",
        human_review_gate="not_required",
    )
    with pytest.raises(ValueError, match="not declared"):
        run_agent(
            agent_dir,
            skill_stubs={
                "alpha-skill": lambda _c: {"evidence_ids": [], "evidence": []},
                "beta-skill": lambda _c: {"evidence_ids": [], "evidence": []},
                "ghost-skill": lambda _c: {"evidence_ids": [], "evidence": []},
            },
            skill_names=["alpha-skill", "ghost-skill"],
            runs_root=tmp_path / "runs",
            observed_at="2026-10-28T12:00:00+00:00",
            run_id="run-undeclared",
        )


def test_skill_names_subset_preserves_declared_order(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path / "agents",
        name="fixture-agent",
        skills="alpha-skill,beta-skill,gamma-skill",
        human_review_gate="not_required",
    )
    calls: list[str] = []

    def track(name: str):
        def _stub(_ctx: dict) -> dict:
            calls.append(name)
            return {"evidence_ids": [name], "evidence": []}

        return _stub

    result = run_agent(
        agent_dir,
        skill_stubs={
            "alpha-skill": track("alpha-skill"),
            "beta-skill": track("beta-skill"),
            "gamma-skill": track("gamma-skill"),
        },
        # Requested out of declared order; runner still uses declared order.
        skill_names=["gamma-skill", "alpha-skill"],
        runs_root=tmp_path / "runs",
        observed_at="2026-10-28T12:00:00+00:00",
        run_id="run-subset-order",
    )
    assert calls == ["alpha-skill", "gamma-skill"]
    assert result.skills_invoked == ["alpha-skill", "gamma-skill"]
