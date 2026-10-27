"""Golden path: schema-validator package — fixture page → outputs + Evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
SKILL_ROOT = (
    Path(__file__).resolve().parents[4]
    / "skills"
    / "technical-foundation"
    / "schema-validator"
)
VALIDATE_SCRIPT = SKILL_ROOT / "scripts" / "validate.py"

EVIDENCE_REQUIRED = {"claim", "source", "observed_at", "confidence"}
CONFIDENCE_VALUES = {"high", "medium", "low", "needs_human_verification"}


def _load_validate():
    spec = importlib.util.spec_from_file_location("schema_validator_validate", VALIDATE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_evidence_shape(evidence: list[dict]) -> None:
    assert evidence, "evidence_requirement full requires at least one Evidence record"
    for item in evidence:
        missing = EVIDENCE_REQUIRED - set(item)
        assert not missing, f"Evidence missing fields: {sorted(missing)}"
        assert item["confidence"] in CONFIDENCE_VALUES
        if item["confidence"] == "needs_human_verification":
            assert item.get("verification_reason"), "NHV requires verification_reason"


@pytest.mark.parametrize(
    "case",
    ["happy", "malformed-jsonld", "contradictory-types"],
)
def test_golden_fixture_cases(case: str) -> None:
    case_dir = FIXTURES / case
    html = (case_dir / "input" / "page.html").read_text(encoding="utf-8")
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    validate = _load_validate()
    result = validate.validate_page(
        html,
        source=f"fixture:{case}/input/page.html",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert result["findings"] == expected["findings"]
    _assert_evidence_shape(result["evidence"])
    assert result["evidence"] == expected["evidence"]
