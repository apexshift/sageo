"""crawl-serp Connector MCP black box: call_tool → recorded HTTP or NHV."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sageo.connectors.crawl_serp import TOOL_NAMES, call_tool
from sageo.testing.recorded_http import load_recorded_http

ROOT = Path(__file__).parent
HTTP = load_recorded_http(ROOT / "http")
EXPECTED = ROOT / "expected"

VALID_ENV = {
    "CRAWL_SERP_API_KEY": "login:password",
    "CRAWL_SERP_BASE_URL": "https://api.dataforseo.com",
}

OBSERVED_AT = "2026-10-28T12:00:00+00:00"


def _expected(name: str) -> dict:
    return json.loads((EXPECTED / f"{name}.json").read_text(encoding="utf-8"))


def test_tool_names_are_sageo_owned_readonly_surface() -> None:
    assert TOOL_NAMES == frozenset(
        {
            "crawl_start_task",
            "crawl_site_summary",
            "crawl_page_issues",
            "serp_google_organic",
        }
    )
    assert "on_page_task_post" not in TOOL_NAMES
    assert "lighthouse_audit" not in TOOL_NAMES
    assert "ai_summary" not in TOOL_NAMES


def test_missing_credentials_refuse_start_with_nhv() -> None:
    result = call_tool(
        "crawl_start_task",
        {"target": "example.com", "max_crawl_pages": 10},
        env={"CRAWL_SERP_BASE_URL": "https://api.dataforseo.com"},
        recorded=HTTP,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.data is None
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "missing_credentials"
    assert result.evidence["source"] == "crawl_serp/crawl_start_task"


@pytest.mark.parametrize(
    ("tool", "arguments", "fixture", "expected_name"),
    [
        (
            "crawl_start_task",
            {
                "target": "example.com",
                "max_crawl_pages": 10,
                "start_url": "https://example.com/",
            },
            "crawl_start_task",
            "crawl_start_task",
        ),
        (
            "crawl_site_summary",
            {"task_id": "task-abc-123"},
            "crawl_site_summary",
            "crawl_site_summary",
        ),
        (
            "crawl_page_issues",
            {"task_id": "task-abc-123", "limit": 100},
            "crawl_page_issues",
            "crawl_page_issues",
        ),
        (
            "serp_google_organic",
            {
                "keyword": "example search",
                "location_code": 2840,
                "language_code": "en",
                "depth": 10,
            },
            "serp_google_organic",
            "serp_google_organic",
        ),
    ],
)
def test_happy_path_per_locked_tool(
    tool: str,
    arguments: dict,
    fixture: str,
    expected_name: str,
) -> None:
    recorded = {tool: HTTP[fixture]}
    result = call_tool(
        tool,
        arguments,
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is True
    assert result.evidence is None
    assert result.data == _expected(expected_name)


def test_task_based_crawl_flow_start_summary_pages() -> None:
    """Fixtures short-circuit: start → finished summary → page issues."""
    recorded = {
        "crawl_start_task": HTTP["crawl_start_task"],
        "crawl_site_summary": HTTP["crawl_site_summary"],
        "crawl_page_issues": HTTP["crawl_page_issues"],
    }
    started = call_tool(
        "crawl_start_task",
        {
            "target": "example.com",
            "max_crawl_pages": 10,
            "start_url": "https://example.com/",
        },
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert started.ok is True
    assert started.data is not None
    task_id = started.data["task_id"]

    summary = call_tool(
        "crawl_site_summary",
        {"task_id": task_id},
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert summary.ok is True
    assert summary.data is not None
    assert summary.data["crawl_progress"] == "finished"

    pages = call_tool(
        "crawl_page_issues",
        {"task_id": task_id, "limit": 100},
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert pages.ok is True
    assert pages.data is not None
    assert pages.data["items"][0]["status_code"] == 404


def test_auth_failed_maps_to_nhv() -> None:
    recorded = {"crawl_start_task": HTTP["auth_failed"]}
    result = call_tool(
        "crawl_start_task",
        {"target": "example.com", "max_crawl_pages": 10},
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "auth_failed"
    assert result.evidence["source"] == "crawl_serp/crawl_start_task"


def test_api_key_without_colon_is_missing_credentials() -> None:
    result = call_tool(
        "serp_google_organic",
        {"keyword": "x", "location_code": 2840},
        env={
            "CRAWL_SERP_API_KEY": "not-a-login-password",
            "CRAWL_SERP_BASE_URL": "https://api.dataforseo.com",
        },
        recorded={"serp_google_organic": HTTP["serp_google_organic"]},
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "missing_credentials"


def test_unknown_tool_rejected() -> None:
    with pytest.raises(ValueError, match="unknown tool"):
        call_tool(
            "ai_summary",
            {},
            env=VALID_ENV,
            recorded=HTTP,
            observed_at=OBSERVED_AT,
        )


def test_call_tool_requires_recorded_transport_in_tests() -> None:
    with pytest.raises(ValueError, match="recorded"):
        call_tool(
            "crawl_site_summary",
            {"task_id": "task-abc-123"},
            env=VALID_ENV,
            recorded=None,
            observed_at=OBSERVED_AT,
        )
