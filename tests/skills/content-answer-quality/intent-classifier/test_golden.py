"""Golden path: intent-classifier — query-page fixtures → findings + Evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sageo.testing import golden as skill_golden

TEST_ROOT = Path(__file__).parent
FIXTURES = TEST_ROOT / "fixtures"
SKILL_ROOT = (
    Path(__file__).resolve().parents[4]
    / "skills"
    / "content-answer-quality"
    / "intent-classifier"
)
CLASSIFY_SCRIPT = SKILL_ROOT / "scripts" / "classify.py"


@pytest.mark.parametrize(
    "case",
    ["happy", "mismatch", "ambiguous-query"],
)
def test_golden_fixture_cases(case: str) -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    case_dir = FIXTURES / case
    query_payload = json.loads(
        (case_dir / "input" / "query.json").read_text(encoding="utf-8")
    )
    html = (case_dir / "input" / "page.html").read_text(encoding="utf-8")
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    classify = skill_golden.load_skill_module(CLASSIFY_SCRIPT, "intent_classifier_classify")
    result = classify.classify_intent(
        query_payload["query"],
        html,
        source_query=f"fixture:{case}/input/query.json",
        source_page=f"fixture:{case}/input/page.html",
        source_bundle=f"fixture:{case}/input",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert result["findings"] == expected["findings"]
    skill_golden.assert_evidence_matches_schema(result["evidence"], schema_path)
    assert result["evidence"] == expected["evidence"]


def test_evidence_schema_file_is_part_of_golden_layout() -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    assert schema_path == TEST_ROOT / "evidence.schema.json"
