"""Release seams: first public 0.1.0 history + current product version."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
CHECKLIST = REPO_ROOT / "docs" / "first-public-release-checklist.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def test_changelog_has_dated_0_1_0_section() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    assert re.search(r"^## \[0\.1\.0\] - 20\d{2}-\d{2}-\d{2}\s*$", text, re.MULTILINE)
    assert "## [Unreleased]" in text


def test_changelog_has_dated_0_1_1_patch_section() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    assert re.search(r"^## \[0\.1\.1\] - 20\d{2}-\d{2}-\d{2}\s*$", text, re.MULTILINE)


def test_pyproject_version_is_current_patch() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match is not None
    assert match.group(1) == "0.1.1"


def test_release_checklist_records_v0_1_0_cut_complete() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "- [x] **CI green:**" in text
    assert "- [x] **CHANGELOG:**" in text
    assert "- [x] **Positioning / no-hype review:**" in text
    assert "- [x] **Cut release:**" in text
    assert "v0.1.0" in text
    assert "releases/tag/v0.1.0" in text
