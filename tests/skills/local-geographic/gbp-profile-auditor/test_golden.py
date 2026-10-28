"""Golden path: gbp-profile-auditor — gbp-fixture → findings + Evidence."""

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
    / "gbp-profile-auditor"
)
AUDIT_SCRIPT = SKILL_ROOT / "scripts" / "audit.py"


@pytest.mark.parametrize(
    "case",
    [
        "happy",
        "incomplete-profile",
        "profile-conflict",
    ],
)
def test_golden_fixture_cases(case: str) -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    case_dir = FIXTURES / case
    profile = json.loads(
        (case_dir / "input" / "profile.json").read_text(encoding="utf-8")
    )
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    audit = skill_golden.load_skill_module(
        AUDIT_SCRIPT, "gbp_profile_auditor_audit"
    )
    result = audit.audit_gbp_profile(
        profile,
        source=f"fixture:{case}/input/profile.json",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert result["findings"] == expected["findings"]
    skill_golden.assert_evidence_matches_schema(result["evidence"], schema_path)
    assert result["evidence"] == expected["evidence"]


def test_evidence_schema_file_is_part_of_golden_layout() -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    assert schema_path == TEST_ROOT / "evidence.schema.json"
