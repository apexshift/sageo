"""Golden path: citation-consistency-checker — listings-nap → findings + Evidence."""

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
    / "local-geographic"
    / "citation-consistency-checker"
)
CHECK_SCRIPT = SKILL_ROOT / "scripts" / "check.py"


@pytest.mark.parametrize(
    "case",
    [
        "happy",
        "thin-listings",
        "nap-mismatch",
        "nap-conflict",
        "incomplete-listing",
    ],
)
def test_golden_fixture_cases(case: str) -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    case_dir = FIXTURES / case
    listings = json.loads(
        (case_dir / "input" / "listings.json").read_text(encoding="utf-8")
    )
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    check = skill_golden.load_skill_module(
        CHECK_SCRIPT, "citation_consistency_checker_check"
    )
    result = check.check_citation_consistency(
        listings,
        source=f"fixture:{case}/input/listings.json",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert result["findings"] == expected["findings"]
    skill_golden.assert_evidence_matches_schema(result["evidence"], schema_path)
    assert result["evidence"] == expected["evidence"]


def test_evidence_schema_file_is_part_of_golden_layout() -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    assert schema_path == TEST_ROOT / "evidence.schema.json"
