"""Version sync seam: product CHANGELOG + valid component semver via contract lint."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from sageo.contract_lint import (
    SEMVER_RE,
    discover_agent_packages,
    discover_skill_packages,
    lint_agent_package,
    lint_orchestrator_package,
    lint_skill_package,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def test_changelog_exists_in_keep_a_changelog_style() -> None:
    assert CHANGELOG.is_file(), "expected root CHANGELOG.md"
    text = CHANGELOG.read_text(encoding="utf-8")
    lower = text.lower()
    assert "changelog" in lower
    assert "keep a changelog" in lower
    assert "semantic versioning" in lower or "semver" in lower
    assert "## [Unreleased]" in text or re.search(r"## \[\d+\.\d+\.\d+\]", text)


def test_changelog_documents_independent_component_versions() -> None:
    text = CHANGELOG.read_text(encoding="utf-8").lower()
    # No lockstep: product CHANGELOG must state component semver is independent.
    assert "independent" in text or "need not" in text or "no lockstep" in text
    assert "metadata.version" in text or "component" in text


def test_product_package_version_is_ready_for_first_tag() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None
    assert SEMVER_RE.match(match.group(1)), match.group(1)


def test_every_shipped_pack_has_valid_semver_metadata_version() -> None:
    def version_of(package: Path, filename: str) -> str:
        text = (package / filename).read_text(encoding="utf-8")
        rest = text[3:]
        end = rest.find("\n---")
        frontmatter = yaml.safe_load(rest[:end])
        return str(frontmatter["metadata"]["version"])

    versions: list[tuple[str, str]] = []
    for package in discover_skill_packages(REPO_ROOT / "skills"):
        versions.append((package.name, version_of(package, "SKILL.md")))
    for package in discover_agent_packages(REPO_ROOT / "agents"):
        versions.append((package.name, version_of(package, "AGENT.md")))
    versions.append(
        ("orchestrator", version_of(REPO_ROOT / "orchestrator", "ORCHESTRATOR.md"))
    )

    assert versions
    for name, version in versions:
        assert SEMVER_RE.match(version), f"{name} has non-semver version {version!r}"

    assert lint_orchestrator_package(REPO_ROOT / "orchestrator") == []
    for package in discover_agent_packages(REPO_ROOT / "agents"):
        assert lint_agent_package(package) == []
    for package in discover_skill_packages(REPO_ROOT / "skills"):
        assert lint_skill_package(package) == []
