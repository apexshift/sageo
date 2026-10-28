"""Golden path: evidence-packager — evidence-bundle → package + findings + Evidence."""

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
    / "measurement-prioritisation"
    / "evidence-packager"
)
PACKAGE_SCRIPT = SKILL_ROOT / "scripts" / "package.py"


@pytest.mark.parametrize(
    "case",
    [
        "happy",
        "empty-bundle",
        "incomplete-evidence",
        "nhv-items",
    ],
)
def test_golden_fixture_cases(case: str) -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    case_dir = FIXTURES / case
    bundle = json.loads(
        (case_dir / "input" / "bundle.json").read_text(encoding="utf-8")
    )
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    packager = skill_golden.load_skill_module(
        PACKAGE_SCRIPT, "evidence_packager_package"
    )
    result = packager.package_evidence(
        bundle,
        source=f"fixture:{case}/input/bundle.json",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert result["package"] == expected["package"]
    assert result["findings"] == expected["findings"]
    skill_golden.assert_evidence_matches_schema(result["evidence"], schema_path)
    assert result["evidence"] == expected["evidence"]


def test_evidence_schema_file_is_part_of_golden_layout() -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    assert schema_path == TEST_ROOT / "evidence.schema.json"
