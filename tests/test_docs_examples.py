"""Doc seam: docs/examples/ index + required example content contracts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "docs" / "examples"
INDEX = EXAMPLES / "README.md"
NATIONAL = EXAMPLES / "national-audit.md"
SKILL_LAYOUT = EXAMPLES / "skill-layout.md"
CONNECTOR_CREDS = EXAMPLES / "connector-credentials.md"


def test_examples_directory_has_index_and_required_files() -> None:
    assert EXAMPLES.is_dir(), "expected docs/examples/"
    assert INDEX.is_file(), "expected docs/examples/README.md index"
    assert NATIONAL.is_file()
    assert SKILL_LAYOUT.is_file()
    assert CONNECTOR_CREDS.is_file()
    index = INDEX.read_text(encoding="utf-8").lower()
    assert "national-audit" in index
    assert "skill" in index
    assert "connector" in index


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
