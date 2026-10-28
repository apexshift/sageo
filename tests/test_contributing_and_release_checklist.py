"""Doc seam: CONTRIBUTING.md + first-public-release checklist content contracts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
CHECKLIST = REPO_ROOT / "docs" / "first-public-release-checklist.md"


def test_contributing_md_covers_public_release_contribution_posture() -> None:
    assert CONTRIBUTING.is_file(), "expected root CONTRIBUTING.md"
    text = CONTRIBUTING.read_text(encoding="utf-8")
    lower = text.lower()

    # Timing: external PRs only after first public release tag.
    assert "first public release" in lower or "first public" in lower
    assert "external" in lower and ("pull request" in lower or "pr" in lower)

    # Propose via issues first.
    assert "issue" in lower
    assert "before" in lower or "first" in lower

    # Outsider scope: Skills + docs/fixes; maintainer-only core layers.
    assert "skill" in lower
    assert "docs" in lower or "documentation" in lower
    assert "maintainer" in lower
    assert "orchestrator" in lower
    assert "connector" in lower
    assert "agent" in lower

    # Pointers: ethics, LICENSE, README.
    assert "ethical-accountability-policy" in text or "ethical accountability" in lower
    assert "LICENSE" in text or "mit" in lower
    assert "README" in text


def test_contributing_skill_bar_uses_glossary_and_ethics_vocabulary() -> None:
    text = CONTRIBUTING.read_text(encoding="utf-8")
    lower = text.lower()

    assert "evidence" in lower
    assert "needs_human_verification" in text or "nhv" in lower
    assert "reach" in lower
    assert "geo" in lower
    assert "white-hat" in lower or "white hat" in lower
    assert "human review" in lower
    assert "guaranteed" in lower  # reject guaranteed-rankings framing
    assert "capability pillar" in lower or "skills/" in text


def test_first_public_release_checklist_gates_tagging() -> None:
    assert CHECKLIST.is_file(), "expected docs/first-public-release-checklist.md"
    text = CHECKLIST.read_text(encoding="utf-8")
    lower = text.lower()

    required_phrases = [
        "ci",
        "lint",
        "contract lint",
        "pytest",
        "e2e",
        "national-audit",
        "metrics",
        "changelog",
        "version",
        "readme",
        "contributing",
        "ethic",
        "mit",
        "license",
        "secret",
        "hype",
        "github release",
    ]
    for phrase in required_phrases:
        assert phrase in lower, f"checklist missing {phrase!r}"

    # Checklist uses Markdown task items (open or completed).
    assert "- [ ]" in text or "- [x]" in text
    # First public cut is complete for v0.1.0.
    assert "- [x] **Cut release:**" in text
    assert "releases/tag/v0.1.0" in text
