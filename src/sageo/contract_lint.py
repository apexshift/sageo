"""Lint Skill, Agent, and Orchestrator packages against locked metadata contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Component metadata.version: MAJOR.MINOR.PATCH with optional pre-release/build.
SEMVER_RE = re.compile(
    r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)

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
COST_MODELS = frozenset(
    {"tokens_and_connector_calls", "tokens_only", "manual_estimate"}
)

REQUIRED_TOP_LEVEL = ("name", "description", "metadata")
REQUIRED_METADATA = (
    "version",
    "capability_pillar",
    "primary_outcome",
    "evidence_requirement",
    "human_review_gate",
)
AGENT_REQUIRED_METADATA = (
    "version",
    "primary_outcome",
    "skills",
    "human_review_gate",
    "cost_model",
)


@dataclass(frozen=True)
class LintIssue:
    """One contract violation for a Skill, Agent, or Orchestrator package."""

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
    issues.extend(_lint_semver_version(metadata, skill_md))
    issues.extend(_lint_enums(metadata, skill_md))
    issues.extend(_lint_path_alignment(skill_dir, frontmatter, metadata, skill_md))
    return issues


def lint_all_skill_packages(skills_root: Path) -> list[LintIssue]:
    """Lint every discovered Skill package under ``skills_root``."""
    issues: list[LintIssue] = []
    for package in discover_skill_packages(skills_root):
        issues.extend(lint_skill_package(package))
    return issues


def discover_agent_packages(agents_root: Path) -> list[Path]:
    """Return Agent package dirs that contain an AGENT.md under ``agents/<name>/``."""
    if not agents_root.is_dir():
        return []
    packages: list[Path] = []
    for agent_md in sorted(agents_root.glob("*/AGENT.md")):
        packages.append(agent_md.parent)
    return packages


def lint_agent_package(agent_dir: Path) -> list[LintIssue]:
    """Validate one Agent package directory; empty list means pass."""
    agent_md = agent_dir / "AGENT.md"
    if not agent_md.is_file():
        return [LintIssue("missing_agent_md", "AGENT.md is required", agent_dir)]

    text = agent_md.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(text)
    if frontmatter is None:
        return [LintIssue("missing_frontmatter", "YAML frontmatter is required", agent_md)]

    issues: list[LintIssue] = []
    issues.extend(_lint_required_fields(frontmatter, agent_md))
    if issues:
        return issues

    metadata = frontmatter["metadata"]
    if not isinstance(metadata, dict):
        return [LintIssue("invalid_metadata", "metadata must be a mapping", agent_md)]

    issues.extend(_lint_agent_required_metadata(metadata, agent_md))
    issues.extend(_lint_semver_version(metadata, agent_md))
    issues.extend(_lint_agent_enums(metadata, agent_md))
    issues.extend(_lint_agent_skills(metadata, agent_md))
    issues.extend(_lint_agent_path_alignment(agent_dir, frontmatter, agent_md))
    return issues


def lint_all_agent_packages(agents_root: Path) -> list[LintIssue]:
    """Lint every discovered Agent package under ``agents_root``."""
    issues: list[LintIssue] = []
    for package in discover_agent_packages(agents_root):
        issues.extend(lint_agent_package(package))
    return issues


def lint_orchestrator_package(orchestrator_dir: Path) -> list[LintIssue]:
    """Validate Orchestrator package metadata (version required)."""
    orch_md = orchestrator_dir / "ORCHESTRATOR.md"
    if not orch_md.is_file():
        return [
            LintIssue(
                "missing_orchestrator_md",
                "ORCHESTRATOR.md is required",
                orchestrator_dir,
            )
        ]
    frontmatter = _parse_frontmatter(orch_md.read_text(encoding="utf-8"))
    if frontmatter is None:
        return [
            LintIssue(
                "missing_frontmatter",
                "YAML frontmatter is required",
                orch_md,
            )
        ]
    issues: list[LintIssue] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in frontmatter or frontmatter[field] in (None, ""):
            issues.append(
                LintIssue(
                    "missing_field",
                    f"missing required field {field!r}",
                    orch_md,
                )
            )
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        issues.append(
            LintIssue("invalid_metadata", "metadata must be a mapping", orch_md)
        )
        return issues
    if "version" not in metadata or metadata["version"] in (None, ""):
        issues.append(
            LintIssue(
                "missing_metadata_field",
                "missing required metadata field 'version'",
                orch_md,
            )
        )
    else:
        issues.extend(_lint_semver_version(metadata, orch_md))
    return issues


def parse_skill_list(skills_value: Any) -> list[str] | None:
    """Parse Agent ``metadata.skills`` into an ordered name list, or None if empty/invalid."""
    if skills_value is None:
        return None
    if isinstance(skills_value, list):
        names = [str(item).strip() for item in skills_value if str(item).strip()]
        return names or None
    if not isinstance(skills_value, str):
        return None
    names = [part.strip() for part in skills_value.split(",") if part.strip()]
    return names or None


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


def _lint_semver_version(metadata: dict[str, Any], path: Path) -> list[LintIssue]:
    """Fail when metadata.version is present but not a valid semver string.

    Absence/empty is reported by the required-metadata helpers as
    ``missing_version`` / ``missing_metadata_field``.
    """
    version = metadata.get("version")
    if version in (None, ""):
        return []
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        return [
            LintIssue(
                "invalid_version",
                "metadata.version must be a semver string (MAJOR.MINOR.PATCH)",
                path,
            )
        ]
    return []


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


def _lint_agent_required_metadata(metadata: dict[str, Any], path: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for field in AGENT_REQUIRED_METADATA:
        if field not in metadata or metadata[field] in (None, ""):
            issues.append(
                LintIssue(f"missing_{field}", f"missing required metadata.{field}", path)
            )
    if "capability_pillar" in metadata:
        issues.append(
            LintIssue(
                "unexpected_capability_pillar",
                "Agents must not set capability_pillar; they span pillars via skills",
                path,
            )
        )
    return issues


def _lint_agent_enums(metadata: dict[str, Any], path: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    outcome = metadata.get("primary_outcome")
    if outcome is not None and outcome not in PRIMARY_OUTCOMES:
        issues.append(
            LintIssue(
                "invalid_primary_outcome",
                f"primary_outcome must be one of {sorted(PRIMARY_OUTCOMES)}",
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

    cost_model = metadata.get("cost_model")
    if cost_model is not None and cost_model not in COST_MODELS:
        issues.append(
            LintIssue(
                "invalid_cost_model",
                f"cost_model must be one of {sorted(COST_MODELS)}",
                path,
            )
        )

    secondary = metadata.get("secondary_outcomes")
    if secondary is not None:
        values: list[str]
        if isinstance(secondary, str):
            values = [part.strip() for part in secondary.split(",") if part.strip()]
        elif isinstance(secondary, list):
            values = [str(item).strip() for item in secondary if str(item).strip()]
        else:
            values = []
            issues.append(
                LintIssue(
                    "invalid_secondary_outcomes",
                    "secondary_outcomes must be a comma-separated string or list",
                    path,
                )
            )
        for value in values:
            if value not in PRIMARY_OUTCOMES:
                issues.append(
                    LintIssue(
                        "invalid_secondary_outcomes",
                        f"secondary_outcomes entries must be one of {sorted(PRIMARY_OUTCOMES)}",
                        path,
                    )
                )
                break
    return issues


def _lint_agent_skills(metadata: dict[str, Any], path: Path) -> list[LintIssue]:
    if "skills" not in metadata or metadata["skills"] in (None, ""):
        return []
    names = parse_skill_list(metadata.get("skills"))
    if names is None:
        return [
            LintIssue(
                "invalid_skills",
                "skills must list at least one Skill name (comma-separated or list)",
                path,
            )
        ]
    return []


def _lint_agent_path_alignment(
    agent_dir: Path,
    frontmatter: dict[str, Any],
    path: Path,
) -> list[LintIssue]:
    name = frontmatter.get("name")
    dir_name = agent_dir.name
    if name is not None and name != dir_name:
        return [
            LintIssue(
                "name_dir_mismatch",
                f"name {name!r} must match directory name {dir_name!r}",
                path,
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    """CLI: lint Skill, Agent, and Orchestrator packages under the repo root."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m sageo.contract_lint",
        description="Lint Skill/Agent/Orchestrator package metadata contracts.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    args = parser.parse_args(argv)
    root: Path = args.root

    issues: list[LintIssue] = []
    issues.extend(lint_all_skill_packages(root / "skills"))
    issues.extend(lint_all_agent_packages(root / "agents"))
    orch_dir = root / "orchestrator"
    if orch_dir.is_dir():
        issues.extend(lint_orchestrator_package(orch_dir))

    for issue in issues:
        print(f"{issue.path}: {issue.code}: {issue.message}", file=sys.stderr)
    if issues:
        print(f"contract lint failed: {len(issues)} issue(s)", file=sys.stderr)
        return 1
    print("contract lint passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
