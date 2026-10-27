"""Shared Skill golden helpers — public test API for Core Skill packages."""

from __future__ import annotations

from pathlib import Path

import pytest

from sageo.testing import golden as skill_golden

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VALIDATOR_TESTS = (
    REPO_ROOT / "tests" / "skills" / "technical-foundation" / "schema-validator"
)


def test_require_evidence_schema_returns_existing_path() -> None:
    schema_path = skill_golden.require_evidence_schema(SCHEMA_VALIDATOR_TESTS)
    assert schema_path.is_file()
    assert schema_path.name == "evidence.schema.json"


def test_require_evidence_schema_fails_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="evidence.schema.json"):
        skill_golden.require_evidence_schema(tmp_path)


def test_assert_evidence_matches_schema_accepts_valid_full_evidence() -> None:
    schema_path = skill_golden.require_evidence_schema(SCHEMA_VALIDATOR_TESTS)
    evidence = [
        {
            "claim": "Example claim",
            "source": "fixture:example",
            "observed_at": "2026-10-27T12:00:00Z",
            "confidence": "high",
        }
    ]
    skill_golden.assert_evidence_matches_schema(evidence, schema_path)


def test_assert_evidence_matches_schema_rejects_nhv_without_reason() -> None:
    schema_path = skill_golden.require_evidence_schema(SCHEMA_VALIDATOR_TESTS)
    evidence = [
        {
            "claim": "Ambiguous claim",
            "source": "fixture:example",
            "observed_at": "2026-10-27T12:00:00Z",
            "confidence": "needs_human_verification",
        }
    ]
    with pytest.raises(Exception):
        skill_golden.assert_evidence_matches_schema(evidence, schema_path)


def test_load_skill_module_exposes_callable() -> None:
    script = (
        REPO_ROOT
        / "skills"
        / "technical-foundation"
        / "schema-validator"
        / "scripts"
        / "validate.py"
    )
    module = skill_golden.load_skill_module(script, "schema_validator_validate")
    assert callable(module.validate_page)
