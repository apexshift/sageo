"""Doc seam: docs/examples/ index + required example content contracts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "docs" / "examples"
INDEX = EXAMPLES / "README.md"
NATIONAL = EXAMPLES / "national-audit.md"
LOCAL = EXAMPLES / "local-workflow.md"
GLOBAL = EXAMPLES / "global-workflow.md"
TECH_ONBOARD = EXAMPLES / "technical-audit-and-onboarding.md"
AFK = EXAMPLES / "afk-automation.md"
SKILL_LAYOUT = EXAMPLES / "skill-layout.md"
CONNECTOR_CREDS = EXAMPLES / "connector-credentials.md"


def test_examples_directory_has_index_and_required_files() -> None:
    assert EXAMPLES.is_dir(), "expected docs/examples/"
    assert INDEX.is_file(), "expected docs/examples/README.md index"
    for path in (
        NATIONAL,
        LOCAL,
        GLOBAL,
        TECH_ONBOARD,
        AFK,
        SKILL_LAYOUT,
        CONNECTOR_CREDS,
    ):
        assert path.is_file(), f"missing {path.relative_to(REPO_ROOT)}"
    index = INDEX.read_text(encoding="utf-8").lower()
    for needle in (
        "national-audit",
        "local-workflow",
        "global-workflow",
        "technical-audit-and-onboarding",
        "afk-automation",
        "skill",
        "connector",
    ):
        assert needle in index, f"index missing {needle!r}"


def test_national_audit_example_covers_routing_gate_logs_and_metrics() -> None:
    text = NATIONAL.read_text(encoding="utf-8")
    lower = text.lower()
    for needle in (
        "technical-findings",
        "content-aio",
        "measurement-evidence",
        "orchestrator",
        "human review",
        "evidence",
        "decision log",
        "metrics",
        "tests/e2e/national-audit",
    ):
        assert needle in lower, f"national-audit example missing {needle!r}"
    assert "guaranteed" not in lower or "no guaranteed" in lower or "not guarantee" in lower


def test_local_workflow_points_at_shipped_local_reach_agent() -> None:
    text = LOCAL.read_text(encoding="utf-8")
    lower = text.lower()
    assert "local-reach" in lower
    assert "agents/local-reach" in text
    assert "gbp-profile-auditor" in lower
    assert "human review" in lower
    assert "tests/agents/local-reach" in text
    assert (REPO_ROOT / "agents" / "local-reach" / "AGENT.md").is_file()


def test_global_workflow_is_reach_pattern_without_invented_agent() -> None:
    text = GLOBAL.read_text(encoding="utf-8")
    lower = text.lower()
    assert "reach" in lower and "global" in lower
    assert "local-reach" in lower
    assert "thin" in lower or "national" in lower
    assert "roadmap" in lower or "not packaged" in lower or "not invent" in lower
    assert "agents/global-reach" not in text


def test_technical_audit_and_onboarding_uses_technical_findings() -> None:
    text = TECH_ONBOARD.read_text(encoding="utf-8")
    lower = text.lower()
    assert "technical-findings" in lower
    assert "onboarding" in lower
    assert "crawl-issue-extractor" in lower
    assert "make ci" in lower
    assert "agents/technical-findings" in text
    assert (REPO_ROOT / "agents" / "technical-findings" / "AGENT.md").is_file()


def test_afk_automation_states_gate_limits_and_no_autopublish() -> None:
    text = AFK.read_text(encoding="utf-8")
    lower = text.lower()
    assert "awaiting_approval" in lower or "human review" in lower
    assert "resume" in lower
    assert "auto-publish" in lower or "live-site" in lower or "live site" in lower
    assert "approved=true" in lower or "approved=True" in text or "real human" in lower
    assert "cron" in lower or "scheduler" in lower or "ops" in lower


def test_skill_layout_example_points_at_real_shipped_skill() -> None:
    text = SKILL_LAYOUT.read_text(encoding="utf-8")
    assert "skills/" in text
    assert "SKILL.md" in text
    assert "schema-validator" in text or "skills/technical-foundation/" in text
    # Real path on disk referenced in the example must exist.
    assert (REPO_ROOT / "skills" / "technical-foundation" / "schema-validator" / "SKILL.md").is_file()
    assert "skills/technical-foundation/schema-validator" in text


def test_connector_credentials_example_uses_env_example_without_secrets() -> None:
    text = CONNECTOR_CREDS.read_text(encoding="utf-8")
    lower = text.lower()
    assert ".env.example" in text
    assert "gsc" in lower or "ga4" in lower or "crawl" in lower
    assert "secret" in lower or "placeholder" in lower or "never commit" in lower
    assert "read-only" in lower or "read only" in lower
    # No private-key / API material shapes.
    assert "BEGIN PRIVATE KEY" not in text
    assert "AIza" not in text
    for line in text.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            _, _, value = line.partition("=")
            assert value.strip() in ("", "…", "...", "<placeholder>"), line
