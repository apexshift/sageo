"""Metrics helper black box: Run directory → metrics.json report."""

from __future__ import annotations

import json
from pathlib import Path

from sageo.metrics import write_run_metrics


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_complete_evidence_run_passes_completeness_and_writes_cost(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-complete"
    run_dir.mkdir()
    _write_jsonl(
        run_dir / "evidence.jsonl",
        [
            {
                "id": "ev-1",
                "claim": "Crawl found one 404.",
                "source": "fixture:crawl",
                "observed_at": "2026-10-28T12:00:00+00:00",
                "confidence": "high",
            }
        ],
    )
    _write_jsonl(
        run_dir / "decision_log.jsonl",
        [
            {
                "decision_id": "d-1",
                "actor": "agent",
                "evidence_ids": ["ev-1"],
                "outcome": "completed",
            }
        ],
    )

    report = write_run_metrics(
        run_dir,
        cost_models=["tokens_and_connector_calls"],
        usage={"tokens": 1200, "connector_calls": 2},
    )

    assert report["evidence_completeness"]["status"] == "pass"
    assert report["evidence_completeness"]["missing_evidence_ids"] == []
    assert report["evidence_completeness"]["nhv_missing_verification_reason"] == []
    assert "cost" in report
    assert report["cost"]["tokens_class"] == "from_usage_stub"
    assert report["cost"]["connector_calls_class"] == "from_usage_stub"
    assert report["cost"]["tokens_estimate"] == 1200
    assert report["cost"]["connector_calls_estimate"] == 2
    dumped = json.dumps(report).lower()
    assert "ranking" not in dumped
    assert "traffic" not in dumped

    written = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert written == report


def test_missing_evidence_id_fails_completeness_with_pointer(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-missing"
    run_dir.mkdir()
    _write_jsonl(
        run_dir / "evidence.jsonl",
        [
            {
                "id": "ev-present",
                "claim": "Present Evidence.",
                "source": "fixture",
                "observed_at": "2026-10-28T12:00:00+00:00",
                "confidence": "high",
            }
        ],
    )
    _write_jsonl(
        run_dir / "decision_log.jsonl",
        [
            {
                "decision_id": "d-missing",
                "actor": "agent",
                "evidence_ids": ["ev-absent"],
                "outcome": "completed",
            }
        ],
    )

    report = write_run_metrics(run_dir, cost_models=["tokens_only"])

    assert report["evidence_completeness"]["status"] == "fail"
    assert report["evidence_completeness"]["missing_evidence_ids"] == [
        {
            "pointer": "decision_log:d-missing",
            "evidence_id": "ev-absent",
            "claim": (
                "Decision 'd-missing' references Evidence id 'ev-absent' "
                "which is absent from evidence.jsonl"
            ),
        }
    ]
    assert (run_dir / "metrics.json").is_file()


def test_nhv_without_verification_reason_fails_completeness(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-nhv"
    run_dir.mkdir()
    _write_jsonl(
        run_dir / "evidence.jsonl",
        [
            {
                "id": "ev-nhv",
                "claim": "Connector failed; claim needs a human.",
                "source": "gsc/search_analytics_query",
                "observed_at": "2026-10-28T12:00:00+00:00",
                "confidence": "needs_human_verification",
            }
        ],
    )
    _write_jsonl(
        run_dir / "decision_log.jsonl",
        [
            {
                "decision_id": "d-nhv",
                "actor": "orchestrator",
                "evidence_ids": ["ev-nhv"],
                "outcome": "ask_human",
            }
        ],
    )

    report = write_run_metrics(run_dir, cost_models=["tokens_only"])

    assert report["evidence_completeness"]["status"] == "fail"
    assert report["evidence_completeness"]["nhv_missing_verification_reason"] == [
        {
            "pointer": "evidence.jsonl:id=ev-nhv",
            "claim": "Connector failed; claim needs a human.",
        }
    ]


def test_cost_section_from_cost_model_without_usage_notes_uncertainty(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-cost-estimate"
    run_dir.mkdir()
    _write_jsonl(run_dir / "evidence.jsonl", [])
    _write_jsonl(run_dir / "decision_log.jsonl", [])

    report = write_run_metrics(
        run_dir,
        cost_models=["tokens_only"],
        invocation_count=3,
    )

    assert report["cost"]["tokens_class"] == "estimated_from_declarations"
    assert report["cost"]["connector_calls_class"] == "not_applicable"
    assert report["cost"]["tokens_estimate"] is None
    assert report["cost"]["invocation_count"] == 3
    assert report["cost"]["uncertainty_notes"]
    assert all(
        "rank" not in note.lower() and "traffic" not in note.lower()
        for note in report["cost"]["uncertainty_notes"]
    )


def test_reads_cost_models_and_invocations_from_run_directory(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run-invocations"
    run_dir.mkdir()
    _write_jsonl(run_dir / "evidence.jsonl", [])
    _write_jsonl(
        run_dir / "decision_log.jsonl",
        [
            {
                "decision_id": "d-skills",
                "actor": "agent",
                "skills": ["crawl-issue-extractor", "indexability-checker"],
                "evidence_ids": [],
                "outcome": "completed",
            }
        ],
    )
    (run_dir / "invocations.json").write_text(
        json.dumps(
            [
                {
                    "component": "technical-findings",
                    "cost_model": "tokens_and_connector_calls",
                },
                {
                    "component": "crawl-issue-extractor",
                    "cost_model": "tokens_and_connector_calls",
                },
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = write_run_metrics(run_dir)

    assert report["cost"]["cost_models"] == ["tokens_and_connector_calls"]
    assert report["cost"]["tokens_class"] == "estimated_from_declarations"
    assert report["cost"]["connector_calls_class"] == "estimated_from_declarations"
    assert report["cost"]["tokens_estimate"] is None
    assert report["cost"]["connector_calls_estimate"] is None
    assert report["cost"]["invocation_count"] == 2
    assert (run_dir / "metrics.json").is_file()
