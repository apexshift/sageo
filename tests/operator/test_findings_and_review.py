"""Operator bridge: Findings list/filters and Review gate snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from sageo.operator import (
    get_review,
    list_findings,
    resume_run_from_checkout,
    start_thin_audit_from_checkout,
)
from sageo.orchestrator import AgentSpec, RunRequest, run


def _write_evidence(run_dir: Path, rows: list[dict]) -> None:
    path = run_dir / "evidence.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _seed_run(tmp_path: Path) -> Path:
    runs_root = tmp_path / "runs"
    agents = [
        AgentSpec(
            name="technical-findings",
            primary_outcome="SEO",
            when_to_use=frozenset({"thin_audit"}),
            pipeline_role="technical",
            execute=lambda _c: {
                "evidence_ids": ["tech-1", "tech-nhv"],
                "evidence": [
                    {
                        "id": "tech-1",
                        "claim": "Crawl errors on /pricing",
                        "source": "crawl-issue-extractor",
                        "observed_at": "2026-10-29T12:00:00+00:00",
                        "confidence": "high",
                        "method": "log-scan",
                        "agent": "technical-findings",
                    },
                    {
                        "id": "tech-nhv",
                        "claim": "Indexability uncertain without live fetch",
                        "source": "gsc/urlInspection",
                        "observed_at": "2026-10-29T12:00:00+00:00",
                        "confidence": "needs_human_verification",
                        "verification_reason": "auth_failed",
                        "agent": "technical-findings",
                    },
                ],
                "status": "completed",
            },
        ),
        AgentSpec(
            name="content-aio",
            primary_outcome="SEO",
            when_to_use=frozenset({"thin_audit"}),
            pipeline_role="content_aio",
            human_review_gate="required",
            execute=lambda _c: {
                "evidence_ids": ["content-1"],
                "evidence": [
                    {
                        "id": "content-1",
                        "claim": "Answer extractability is weak",
                        "source": "answer-extractability-scorer",
                        "observed_at": "2026-10-29T12:01:00+00:00",
                        "confidence": "medium",
                        "agent": "content-aio",
                    }
                ],
                "status": "completed",
            },
        ),
    ]
    result = run(
        RunRequest(
            goal="Audit",
            intent="thin_audit",
            primary_outcome="SEO",
            property_refs={"site_url": "https://example.com/"},
            reach="national",
            playbook="thin_audit",
        ),
        agents,
        runs_root=runs_root,
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-findings",
    )
    # Gate stops before content-aio execute; seed its evidence for filter tests.
    existing = [
        json.loads(line)
        for line in (result.run_dir / "evidence.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    _write_evidence(
        result.run_dir,
        existing
        + [
            {
                "id": "content-1",
                "claim": "Answer extractability is weak",
                "source": "answer-extractability-scorer",
                "observed_at": "2026-10-29T12:01:00+00:00",
                "confidence": "medium",
                "agent": "content-aio",
            }
        ],
    )
    return result.run_dir


def test_list_findings_rows_and_nhv_detail(tmp_path: Path) -> None:
    run_dir = _seed_run(tmp_path)
    rows = list_findings(run_dir.parent, "run-findings")
    assert len(rows) == 3
    by_id = {row.id: row for row in rows}
    assert by_id["tech-1"].title == "Crawl errors on /pricing"
    assert by_id["tech-1"].agent == "technical-findings"
    assert by_id["tech-1"].confidence == "high"
    assert by_id["tech-1"].is_nhv is False
    assert by_id["tech-1"].method == "log-scan"
    assert by_id["tech-1"].source == "crawl-issue-extractor"
    assert by_id["tech-1"].observed_at == "2026-10-29T12:00:00+00:00"

    nhv = by_id["tech-nhv"]
    assert nhv.is_nhv is True
    assert nhv.confidence == "needs_human_verification"
    assert nhv.verification_reason == "auth_failed"
    assert nhv.confidence != "high"


def test_list_findings_filters_confidence_and_agent(tmp_path: Path) -> None:
    run_dir = _seed_run(tmp_path)
    runs_root = run_dir.parent
    nhv_only = list_findings(
        runs_root, "run-findings", confidence="needs_human_verification"
    )
    assert [r.id for r in nhv_only] == ["tech-nhv"]
    assert all(r.is_nhv for r in nhv_only)

    agent_only = list_findings(
        runs_root, "run-findings", agent="content-aio"
    )
    assert [r.id for r in agent_only] == ["content-1"]

    both = list_findings(
        runs_root,
        "run-findings",
        confidence="high",
        agent="technical-findings",
    )
    assert [r.id for r in both] == ["tech-1"]

    assert len(list_findings(runs_root, "run-findings")) == 3


def test_get_review_when_gate_open(tmp_path: Path) -> None:
    _seed_run(tmp_path)
    review = get_review(tmp_path / "runs", "run-findings")
    assert review.gate_open is True
    assert review.gate_state == "awaiting_approval"
    assert review.paused_agent == "content-aio"
    assert review.empty_message is None
    assert review.decision is not None
    assert review.decision.get("kind") == "gate"
    assert "content-aio" in (review.decision.get("agents") or [])
    assert "tech-1" in review.evidence_ids or "tech-nhv" in review.evidence_ids
    linked_ids = {f.id for f in review.linked_findings}
    assert linked_ids <= {f.id for f in list_findings(tmp_path / "runs", "run-findings")}


def test_get_review_empty_when_no_gate(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "run-closed"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "request": {
                    "goal": "done",
                    "intent": "thin_audit",
                    "primary_outcome": "SEO",
                    "property_refs": {"site_url": "https://example.com/"},
                    "reach": "national",
                    "playbook": "thin_audit",
                },
                "schedule": ["technical-findings"],
                "gate_state": "closed",
                "paused_agent": None,
                "agent_statuses": [{"name": "technical-findings", "status": "completed"}],
                "evidence_refs": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "decision_log.jsonl").write_text("", encoding="utf-8")
    (run_dir / "evidence.jsonl").write_text("", encoding="utf-8")

    review = get_review(runs_root, "run-closed")
    assert review.gate_open is False
    assert review.paused_agent is None
    assert review.empty_message
    assert "gate" in review.empty_message.lower()


def _checkout_agents(root: Path) -> Path:
    import yaml

    checkout = root / "checkout"
    (checkout / "orchestrator").mkdir(parents=True)
    agents = checkout / "agents"
    for name, gate in (
        ("technical-findings", "not_required"),
        ("content-aio", "required"),
        ("local-reach", "required"),
        ("measurement-evidence", "required"),
    ):
        agent_dir = agents / name
        agent_dir.mkdir(parents=True)
        frontmatter = {
            "name": name,
            "description": name,
            "metadata": {
                "version": "0.1.0",
                "primary_outcome": "SEO",
                "skills": "alpha-skill",
                "human_review_gate": gate,
                "cost_model": "tokens_only",
            },
        }
        fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
        (agent_dir / "AGENT.md").write_text(
            f"---\n{fm}\n---\n\n## Purpose\n\nFixture.\n",
            encoding="utf-8",
        )
    return checkout


def test_resume_from_checkout_approve_with_note(tmp_path: Path) -> None:
    checkout = _checkout_agents(tmp_path)
    runs_root = tmp_path / "runs"
    started = start_thin_audit_from_checkout(
        checkout_root=checkout,
        runs_root=runs_root,
        site_url="https://example.com/",
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-resume-review",
    )
    assert started.gate_state == "awaiting_approval"
    review = get_review(runs_root, "run-resume-review")
    assert review.gate_open is True

    result = resume_run_from_checkout(
        checkout_root=checkout,
        runs_root=runs_root,
        run_id="run-resume-review",
        approved=True,
        observed_at="2026-10-29T12:05:00+00:00",
        operator_note="Looks good",
    )
    assert result.gate_state in {"closed", "awaiting_approval"}
    after = get_review(runs_root, "run-resume-review")
    log = (runs_root / "run-resume-review" / "decision_log.jsonl").read_text(
        encoding="utf-8"
    )
    assert "Looks good" in log
    assert '"operator_note": "Looks good"' in log
    # After approve, either closed or next gate — Review reflects gate_state.
    assert after.gate_state == result.gate_state


def test_orchestrator_persists_execute_evidence(tmp_path: Path) -> None:
    result = run(
        RunRequest(
            goal="Persist evidence",
            intent="thin_audit",
            primary_outcome="SEO",
            property_refs={"site_url": "https://example.com/"},
            playbook="thin_audit",
        ),
        [
            AgentSpec(
                name="technical-findings",
                primary_outcome="SEO",
                when_to_use=frozenset({"x"}),
                pipeline_role="technical",
                execute=lambda _c: {
                    "evidence_ids": ["e1"],
                    "evidence": [
                        {
                            "id": "e1",
                            "claim": "Persisted claim",
                            "source": "stub",
                            "observed_at": "t",
                            "confidence": "high",
                        }
                    ],
                    "status": "completed",
                },
            )
        ],
        runs_root=tmp_path / "runs",
        observed_at="2026-10-29T12:00:00+00:00",
        run_id="run-persist",
    )
    rows = list_findings(tmp_path / "runs", "run-persist")
    assert len(rows) == 1
    assert rows[0].claim == "Persisted claim"
    assert rows[0].agent == "technical-findings"
    assert result.gate_state == "closed"
