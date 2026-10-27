"""Golden path: mention-sentiment-screener — corpus → findings + Evidence."""

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
    / "authority-trust"
    / "mention-sentiment-screener"
)
SCREEN_SCRIPT = SKILL_ROOT / "scripts" / "screen.py"


@pytest.mark.parametrize(
    "case",
    ["happy", "thin-corpus", "signal-conflict", "negative-risk"],
)
def test_golden_fixture_cases(case: str) -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    case_dir = FIXTURES / case
    corpus = json.loads((case_dir / "input" / "corpus.json").read_text(encoding="utf-8"))
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    screen = skill_golden.load_skill_module(
        SCREEN_SCRIPT, "mention_sentiment_screener_screen"
    )
    result = screen.screen_mention_sentiment(
        corpus,
        source=f"fixture:{case}/input/corpus.json",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert result["findings"] == expected["findings"]
    skill_golden.assert_evidence_matches_schema(result["evidence"], schema_path)
    assert result["evidence"] == expected["evidence"]


def test_evidence_schema_file_is_part_of_golden_layout() -> None:
    schema_path = skill_golden.require_evidence_schema(TEST_ROOT)
    assert schema_path == TEST_ROOT / "evidence.schema.json"
