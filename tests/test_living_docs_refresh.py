"""Living-docs seam: README docs table + anti-staleness content contracts."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
ARCHITECTURE = REPO_ROOT / "docs" / "architecture.md"
GLOSSARY = REPO_ROOT / "GLOSSARY.md"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
EXAMPLES_README = REPO_ROOT / "docs" / "examples" / "README.md"
OPERATOR_EXAMPLE = REPO_ROOT / "docs" / "examples" / "operator-desktop.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"


def test_readme_has_documentation_table_with_useful_links() -> None:
    text = README.read_text(encoding="utf-8")
    assert re.search(r"^##\s+Documentation\b", text, re.MULTILINE)
    # Markdown table with Doc | Description style links.
    assert "| Doc |" in text or "| Document |" in text
    required_links = [
        "docs/architecture.md",
        "docs/ethical-accountability-policy.md",
        "CONTRIBUTING.md",
        "GLOSSARY.md",
        "docs/examples/",
        "docs/first-public-release-checklist.md",
        "CHANGELOG.md",
        "apps/operator-desktop/README.md",
    ]
    for link in required_links:
        assert link in text, f"README docs table missing link to {link}"


def test_readme_quickstart_and_layout_match_current_project() -> None:
    text = README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "make ci" in lower
    assert "placeholder in p1" not in lower
    assert "connectors land in p3" not in lower
    assert "p1 template skill" not in lower
    assert "agents/" in text
    assert "connectors/" in text
    assert "orchestrator/" in text
    assert "apps/" in text
    assert "operator-desktop" in lower
    assert "findings" in lower
    assert "review" in lower
    # Layout should describe real shipped surfaces, not placeholders.
    layout_match = re.search(r"```text\n(.*?)```", text, re.DOTALL)
    assert layout_match is not None
    layout = layout_match.group(1).lower()
    assert "placeholder" not in layout
    assert "apps/" in layout
    assert "wizard + app chrome" not in layout


def test_architecture_roadmap_reflects_shipped_through_p5() -> None:
    text = ARCHITECTURE.read_text(encoding="utf-8")
    lower = text.lower()
    assert "phase roadmap" in lower or "p1–p5" in lower or "p1-p5" in lower
    assert "first public" in lower or "public tag" in lower or "public release" in lower
    # Should not read as if Agents/Connectors are still future-only placeholders.
    assert "placeholder in p1" not in lower
    assert "shipped" in lower or "complete" in lower or "done" in lower


def test_architecture_covers_operator_surface_and_property_refs() -> None:
    text = ARCHITECTURE.read_text(encoding="utf-8")
    lower = text.lower()
    assert "apps/" in text
    assert "operator" in lower
    assert "property refs" in lower or "property_refs" in lower
    assert "site_url" in text
    assert "findings" in lower
    assert "sageo.operator" in text or "operator bridge" in lower


def test_glossary_defines_property_refs_and_finding() -> None:
    text = GLOSSARY.read_text(encoding="utf-8")
    lower = text.lower()
    assert "property refs" in lower
    assert "site_url" in text
    assert "finding" in lower
    assert "evidence" in lower


def test_examples_index_and_operator_desktop_walkthrough() -> None:
    index = EXAMPLES_README.read_text(encoding="utf-8")
    assert "operator-desktop.md" in index
    assert OPERATOR_EXAMPLE.is_file()
    body = OPERATOR_EXAMPLE.read_text(encoding="utf-8").lower()
    assert "sageo.operator" in body or "list-findings" in body
    assert "property refs" in body or "site_url" in body
    assert "review" in body


def test_contributing_reflects_public_release_and_operator_maintainer_only() -> None:
    text = CONTRIBUTING.read_text(encoding="utf-8")
    lower = text.lower()
    assert "v0.1.0" in text
    assert "until that tag exists" not in lower
    assert "operator" in lower
    assert "maintainer-only" in lower or "maintainer only" in lower


def test_env_example_no_longer_says_connectors_land_in_p3() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8").lower()
    assert "connectors land in p3" not in text
    assert "read-only" in text or "read only" in text
