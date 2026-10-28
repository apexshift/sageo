"""Contract lint seam: Agent packages pass or fail on AGENT.md frontmatter."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sageo.contract_lint import (
    LintIssue,
    discover_agent_packages,
    lint_agent_package,
    lint_all_agent_packages,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = REPO_ROOT / "agents"


def _write_agent(
    root: Path,
    *,
    name: str,
    frontmatter: dict,
    body: str = "## Purpose\n\nTest agent.\n",
) -> Path:
    agent_dir = root / name
    agent_dir.mkdir(parents=True)
    fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    (agent_dir / "AGENT.md").write_text(f"---\n{fm}\n---\n\n{body}", encoding="utf-8")
    return agent_dir


def _valid_frontmatter(*, name: str = "example-agent") -> dict:
    return {
        "name": name,
        "description": "Example workflow Agent for contract lint fixtures.",
        "metadata": {
            "version": "0.1.0",
            "primary_outcome": "SEO",
            "skills": "skill-a,skill-b",
            "human_review_gate": "not_required",
            "cost_model": "tokens_and_connector_calls",
        },
    }


def test_discover_finds_nothing_while_agents_are_placeholder() -> None:
    packages = discover_agent_packages(AGENTS_ROOT)
    assert packages == []


def test_lint_accepts_valid_minimal_package(tmp_path: Path) -> None:
    agent_dir = _write_agent(
        tmp_path,
        name="example-agent",
        frontmatter=_valid_frontmatter(),
    )
    assert lint_agent_package(agent_dir) == []


def test_lint_accepts_optional_secondary_outcomes(tmp_path: Path) -> None:
    fm = _valid_frontmatter()
    fm["metadata"]["secondary_outcomes"] = "AIO, GEO"
    agent_dir = _write_agent(tmp_path, name="example-agent", frontmatter=fm)
    assert lint_agent_package(agent_dir) == []


def test_lint_all_agent_packages_empty_root(tmp_path: Path) -> None:
    assert lint_all_agent_packages(tmp_path) == []


def test_lint_all_reports_issues_from_discovered_packages(tmp_path: Path) -> None:
    bad = _valid_frontmatter()
    bad["metadata"].pop("cost_model")
    _write_agent(tmp_path, name="example-agent", frontmatter=bad)
    issues = lint_all_agent_packages(tmp_path)
    assert any(i.code == "missing_cost_model" for i in issues)


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda fm: fm.pop("name"), "missing_name"),
        (lambda fm: fm.pop("description"), "missing_description"),
        (lambda fm: fm["metadata"].pop("version"), "missing_version"),
        (lambda fm: fm["metadata"].pop("primary_outcome"), "missing_primary_outcome"),
        (lambda fm: fm["metadata"].pop("skills"), "missing_skills"),
        (lambda fm: fm["metadata"].pop("human_review_gate"), "missing_human_review_gate"),
        (lambda fm: fm["metadata"].pop("cost_model"), "missing_cost_model"),
        (lambda fm: fm["metadata"].__setitem__("primary_outcome", "SERP"), "invalid_primary_outcome"),
        (
            lambda fm: fm["metadata"].__setitem__("human_review_gate", "optional"),
            "invalid_human_review_gate",
        ),
        (
            lambda fm: fm["metadata"].__setitem__("cost_model", "unlimited"),
            "invalid_cost_model",
        ),
        (lambda fm: fm["metadata"].__setitem__("skills", ""), "missing_skills"),
        (lambda fm: fm["metadata"].__setitem__("skills", "  ,  "), "invalid_skills"),
        (lambda fm: fm.__setitem__("name", "other-name"), "name_dir_mismatch"),
        (
            lambda fm: fm["metadata"].__setitem__("capability_pillar", "technical-foundation"),
            "unexpected_capability_pillar",
        ),
    ],
)
def test_lint_rejects_invalid_packages(tmp_path: Path, mutate, code: str) -> None:
    fm = _valid_frontmatter(name="example-agent")
    mutate(fm)
    agent_dir = _write_agent(tmp_path, name="example-agent", frontmatter=fm)
    issues = lint_agent_package(agent_dir)
    assert issues, f"expected failures for {code}"
    assert any(isinstance(i, LintIssue) and i.code == code for i in issues)


def test_lint_rejects_missing_agent_md(tmp_path: Path) -> None:
    agent_dir = tmp_path / "example-agent"
    agent_dir.mkdir(parents=True)
    issues = lint_agent_package(agent_dir)
    assert any(i.code == "missing_agent_md" for i in issues)


def test_lint_rejects_missing_frontmatter(tmp_path: Path) -> None:
    agent_dir = tmp_path / "example-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "AGENT.md").write_text("## Purpose\n\nNo frontmatter.\n", encoding="utf-8")
    issues = lint_agent_package(agent_dir)
    assert any(i.code == "missing_frontmatter" for i in issues)


def test_lint_rejects_invalid_secondary_outcome(tmp_path: Path) -> None:
    fm = _valid_frontmatter()
    fm["metadata"]["secondary_outcomes"] = "AIO, SERP"
    agent_dir = _write_agent(tmp_path, name="example-agent", frontmatter=fm)
    issues = lint_agent_package(agent_dir)
    assert any(i.code == "invalid_secondary_outcomes" for i in issues)
