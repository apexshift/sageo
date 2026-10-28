"""GSC Connector MCP black box: call_tool → recorded HTTP or NHV Evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sageo.connectors.gsc import TOOL_NAMES, call_tool
from sageo.testing.recorded_http import load_recorded_http

ROOT = Path(__file__).parent
HTTP = load_recorded_http(ROOT / "http")
EXPECTED = ROOT / "expected"

VALID_ENV = {
    "GSC_CLIENT_EMAIL": "sa@example.com",
    "GSC_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----\n",
    "GSC_PROPERTY_URL": "https://example.com/",
}

OBSERVED_AT = "2026-10-28T12:00:00+00:00"


def _expected(name: str) -> dict:
    return json.loads((EXPECTED / f"{name}.json").read_text(encoding="utf-8"))


def test_tool_names_are_sageo_owned_readonly_surface() -> None:
    assert TOOL_NAMES == frozenset(
        {
            "gsc_search_analytics_query",
            "gsc_url_inspect",
            "gsc_sitemaps_list",
        }
    )
    assert "gsc_sitemaps_submit" not in TOOL_NAMES
    assert "gsc_sites_add" not in TOOL_NAMES


def test_missing_credentials_refuse_start_with_nhv() -> None:
    result = call_tool(
        "gsc_sitemaps_list",
        {},
        env={"GSC_CLIENT_EMAIL": "sa@example.com"},
        recorded=HTTP,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.data is None
    assert result.evidence is not None
    assert result.evidence["confidence"] == "needs_human_verification"
    assert result.evidence["verification_reason"] == "missing_credentials"
    assert result.evidence["source"] == "gsc/gsc_sitemaps_list"


@pytest.mark.parametrize(
    ("tool", "arguments", "fixture", "expected_name"),
    [
        (
            "gsc_search_analytics_query",
            {
                "startDate": "2026-10-01",
                "endDate": "2026-10-07",
                "dimensions": ["query"],
            },
            "search_analytics",
            "search_analytics",
        ),
        (
            "gsc_url_inspect",
            {"inspectionUrl": "https://example.com/page"},
            "url_inspect",
            "url_inspect",
        ),
        (
            "gsc_sitemaps_list",
            {},
            "sitemaps_list",
            "sitemaps_list",
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


def test_auth_failed_maps_to_nhv() -> None:
    recorded = {"gsc_search_analytics_query": HTTP["auth_failed"]}
    result = call_tool(
        "gsc_search_analytics_query",
        {"startDate": "2026-10-01", "endDate": "2026-10-07"},
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.data is None
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "auth_failed"
    assert result.evidence["source"] == "gsc/gsc_search_analytics_query"


def test_empty_search_analytics_maps_to_empty_result_nhv() -> None:
    recorded = {"gsc_search_analytics_query": HTTP["empty_search_analytics"]}
    result = call_tool(
        "gsc_search_analytics_query",
        {"startDate": "2026-10-01", "endDate": "2026-10-07"},
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "empty_result"


def test_unknown_tool_rejected() -> None:
    with pytest.raises(ValueError, match="unknown tool"):
        call_tool(
            "gsc_sitemaps_submit",
            {"feedpath": "https://example.com/sitemap.xml"},
            env=VALID_ENV,
            recorded=HTTP,
            observed_at=OBSERVED_AT,
        )


def test_call_tool_requires_recorded_transport_in_tests() -> None:
    """Default CI path must not open live Google sockets."""
    with pytest.raises(ValueError, match="recorded"):
        call_tool(
            "gsc_sitemaps_list",
            {},
            env=VALID_ENV,
            recorded=None,
            observed_at=OBSERVED_AT,
        )
