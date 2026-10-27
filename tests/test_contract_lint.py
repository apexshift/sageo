"""Contract lint seam: Skill packages pass or fail on frontmatter validity."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sageo.contract_lint import (
    LintIssue,
    discover_skill_packages,
    lint_all_skill_packages,
    lint_skill_package,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"


def _write_skill(
    root: Path,
    *,
    pillar: str,
    name: str,
    frontmatter: dict,
    body: str = "## Purpose\n\nTest skill.\n",
) -> Path:
    skill_dir = root / pillar / name
    skill_dir.mkdir(parents=True)
    fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    (skill_dir / "SKILL.md").write_text(f"---\n{fm}\n---\n\n{body}", encoding="utf-8")
    return skill_dir


def _valid_frontmatter(*, name: str = "schema-validator", pillar: str = "technical-foundation") -> dict:
    return {
        "name": name,
        "description": "Validate schema/structured data on a page fixture and emit Evidence.",
        "metadata": {
            "version": "0.1.0",
            "capability_pillar": pillar,
            "primary_outcome": "SEO",
            "evidence_requirement": "full",
            "human_review_gate": "not_required",
        },
    }


def test_discover_finds_schema_validator() -> None:
    packages = discover_skill_packages(SKILLS_ROOT)
    assert any(p.name == "schema-validator" for p in packages)


def test_schema_validator_package_passes_contract_lint() -> None:
    skill_dir = SKILLS_ROOT / "technical-foundation" / "schema-validator"
    assert lint_skill_package(skill_dir) == []


def test_lint_all_skills_has_no_issues() -> None:
    assert lint_all_skill_packages(SKILLS_ROOT) == []


def test_lint_accepts_valid_minimal_package(tmp_path: Path) -> None:
    skill_dir = _write_skill(
        tmp_path,
        pillar="technical-foundation",
        name="schema-validator",
        frontmatter=_valid_frontmatter(),
    )
    assert lint_skill_package(skill_dir) == []


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda fm: fm.pop("name"), "missing_name"),
        (lambda fm: fm.pop("description"), "missing_description"),
        (lambda fm: fm["metadata"].pop("version"), "missing_version"),
        (lambda fm: fm["metadata"].pop("capability_pillar"), "missing_capability_pillar"),
        (lambda fm: fm["metadata"].pop("primary_outcome"), "missing_primary_outcome"),
        (lambda fm: fm["metadata"].pop("evidence_requirement"), "missing_evidence_requirement"),
        (lambda fm: fm["metadata"].pop("human_review_gate"), "missing_human_review_gate"),
        (lambda fm: fm["metadata"].__setitem__("primary_outcome", "SERP"), "invalid_primary_outcome"),
        (lambda fm: fm["metadata"].__setitem__("evidence_requirement", "all"), "invalid_evidence_requirement"),
        (lambda fm: fm["metadata"].__setitem__("human_review_gate", "optional"), "invalid_human_review_gate"),
        (lambda fm: fm["metadata"].__setitem__("capability_pillar", "technical-foundation"), "pillar_path_mismatch"),
        (lambda fm: fm.__setitem__("name", "other-name"), "name_dir_mismatch"),
    ],
)
def test_lint_rejects_invalid_packages(tmp_path: Path, mutate, code: str) -> None:
    pillar = "content-answer-quality" if code == "pillar_path_mismatch" else "technical-foundation"
    name = "schema-validator"
    fm = _valid_frontmatter(name=name, pillar="technical-foundation")
    mutate(fm)
    skill_dir = _write_skill(tmp_path, pillar=pillar, name=name, frontmatter=fm)
    issues = lint_skill_package(skill_dir)
    assert issues, f"expected failures for {code}"
    assert any(isinstance(i, LintIssue) and i.code == code for i in issues)


def test_lint_rejects_missing_skill_md(tmp_path: Path) -> None:
    skill_dir = tmp_path / "technical-foundation" / "schema-validator"
    skill_dir.mkdir(parents=True)
    issues = lint_skill_package(skill_dir)
    assert any(i.code == "missing_skill_md" for i in issues)


def test_lint_rejects_missing_frontmatter(tmp_path: Path) -> None:
    skill_dir = tmp_path / "technical-foundation" / "schema-validator"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("## Purpose\n\nNo frontmatter.\n", encoding="utf-8")
    issues = lint_skill_package(skill_dir)
    assert any(i.code == "missing_frontmatter" for i in issues)
