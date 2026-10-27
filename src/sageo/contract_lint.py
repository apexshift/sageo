"""Lint Skill packages against the locked SKILL.md metadata contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CAPABILITY_PILLARS = frozenset(
    {
        "technical-foundation",
        "content-answer-quality",
        "authority-trust",
        "measurement-prioritisation",
        "local-geographic",
    }
)
PRIMARY_OUTCOMES = frozenset({"SEO", "AIO", "GEO"})
EVIDENCE_REQUIREMENTS = frozenset({"full", "partial", "none"})
HUMAN_REVIEW_GATES = frozenset({"required", "not_required"})

REQUIRED_TOP_LEVEL = ("name", "description", "metadata")
REQUIRED_METADATA = (
    "version",
    "capability_pillar",
    "primary_outcome",
    "evidence_requirement",
    "human_review_gate",
)


@dataclass(frozen=True)
class LintIssue:
    """One contract violation for a Skill package."""

    code: str
    message: str
    path: Path


def discover_skill_packages(skills_root: Path) -> list[Path]:
    """Return Skill package dirs that contain a SKILL.md under ``skills/<pillar>/<name>/``."""
    if not skills_root.is_dir():
        return []
    packages: list[Path] = []
    for skill_md in sorted(skills_root.glob("*/*/SKILL.md")):
        packages.append(skill_md.parent)
    return packages


def lint_skill_package(skill_dir: Path) -> list[LintIssue]:
    """Validate one Skill package directory; empty list means pass."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [LintIssue("missing_skill_md", "SKILL.md is required", skill_dir)]

    text = skill_md.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(text)
    if frontmatter is None:
        return [LintIssue("missing_frontmatter", "YAML frontmatter is required", skill_md)]

    issues: list[LintIssue] = []
    issues.extend(_lint_required_fields(frontmatter, skill_md))
    if issues:
        return issues

    metadata = frontmatter["metadata"]
    if not isinstance(metadata, dict):
        return [LintIssue("invalid_metadata", "metadata must be a mapping", skill_md)]

    issues.extend(_lint_required_metadata(metadata, skill_md))
    issues.extend(_lint_enums(metadata, skill_md))
    issues.extend(_lint_path_alignment(skill_dir, frontmatter, metadata, skill_md))
    return issues


def lint_all_skill_packages(skills_root: Path) -> list[LintIssue]:
    """Lint every discovered Skill package under ``skills_root``."""
    issues: list[LintIssue] = []
    for package in discover_skill_packages(skills_root):
        issues.extend(lint_skill_package(package))
    return issues


def _parse_frontmatter(text: str) -> dict[str, Any] | None:
    if not text.startswith("---"):
        return None
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return None
    raw = rest[:end]
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        return None
    return data


def _lint_required_fields(frontmatter: dict[str, Any], path: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in frontmatter or frontmatter[field] in (None, ""):
            issues.append(LintIssue(f"missing_{field}", f"missing required field: {field}", path))
    return issues


def _lint_required_metadata(metadata: dict[str, Any], path: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for field in REQUIRED_METADATA:
        if field not in metadata or metadata[field] in (None, ""):
            issues.append(LintIssue(f"missing_{field}", f"missing required metadata.{field}", path))
    return issues


def _lint_enums(metadata: dict[str, Any], path: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    pillar = metadata.get("capability_pillar")
    if pillar is not None and pillar not in CAPABILITY_PILLARS:
        issues.append(
            LintIssue(
                "invalid_capability_pillar",
                f"capability_pillar must be one of {sorted(CAPABILITY_PILLARS)}",
                path,
            )
        )

    outcome = metadata.get("primary_outcome")
    if outcome is not None and outcome not in PRIMARY_OUTCOMES:
        issues.append(
            LintIssue(
                "invalid_primary_outcome",
                f"primary_outcome must be one of {sorted(PRIMARY_OUTCOMES)}",
                path,
            )
        )

    evidence = metadata.get("evidence_requirement")
    if evidence is not None and evidence not in EVIDENCE_REQUIREMENTS:
        issues.append(
            LintIssue(
                "invalid_evidence_requirement",
                f"evidence_requirement must be one of {sorted(EVIDENCE_REQUIREMENTS)}",
                path,
            )
        )

    gate = metadata.get("human_review_gate")
    if gate is not None and gate not in HUMAN_REVIEW_GATES:
        issues.append(
            LintIssue(
                "invalid_human_review_gate",
                f"human_review_gate must be one of {sorted(HUMAN_REVIEW_GATES)}",
                path,
            )
        )
    return issues


def _lint_path_alignment(
    skill_dir: Path,
    frontmatter: dict[str, Any],
    metadata: dict[str, Any],
    path: Path,
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    dir_name = skill_dir.name
    pillar_dir = skill_dir.parent.name

    name = frontmatter.get("name")
    if name is not None and name != dir_name:
        issues.append(
            LintIssue(
                "name_dir_mismatch",
                f"name {name!r} must match directory name {dir_name!r}",
                path,
            )
        )

    pillar = metadata.get("capability_pillar")
    if pillar is not None and pillar != pillar_dir:
        issues.append(
            LintIssue(
                "pillar_path_mismatch",
                f"capability_pillar {pillar!r} must match path pillar {pillar_dir!r}",
                path,
            )
        )
    return issues
