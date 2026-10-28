"""GA4 Connector MCP black box: call_tool → recorded HTTP or NHV Evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sageo.connectors.ga4 import TOOL_NAMES, call_tool
from sageo.testing.recorded_http import load_recorded_http

ROOT = Path(__file__).parent
HTTP = load_recorded_http(ROOT / "http")
EXPECTED = ROOT / "expected"

VALID_ENV = {
    "GA4_PROPERTY_ID": "123456789",
    "GA4_CREDENTIALS_JSON": '{"type":"service_account","client_email":"sa@example.com"}',
}

OBSERVED_AT = "2026-10-28T12:00:00+00:00"


def _expected(name: str) -> dict:
    return json.loads((EXPECTED / f"{name}.json").read_text(encoding="utf-8"))


def test_tool_names_are_sageo_owned_readonly_surface() -> None:
    assert TOOL_NAMES == frozenset({"ga4_run_report", "ga4_get_metadata"})
    assert "ga4_run_realtime_report" not in TOOL_NAMES
    assert "ga4_admin_create_property" not in TOOL_NAMES
    assert "ga4_measurement_protocol" not in TOOL_NAMES


def test_missing_credentials_refuse_start_with_nhv() -> None:
    result = call_tool(
        "ga4_get_metadata",
        {},
        env={"GA4_PROPERTY_ID": "123456789"},
        recorded=HTTP,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.data is None
    assert result.evidence is not None
    assert result.evidence["confidence"] == "needs_human_verification"
    assert result.evidence["verification_reason"] == "missing_credentials"
    assert result.evidence["source"] == "ga4/ga4_get_metadata"


@pytest.mark.parametrize(
    ("tool", "arguments", "fixture", "expected_name"),
    [
        (
            "ga4_run_report",
            {
                "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-07"}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
                "metrics": [{"name": "sessions"}],
            },
            "run_report",
            "run_report",
        ),
        (
            "ga4_get_metadata",
            {},
            "get_metadata",
            "get_metadata",
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
    recorded = {"ga4_run_report": HTTP["auth_failed"]}
    result = call_tool(
        "ga4_run_report",
        {
            "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-07"}],
            "metrics": [{"name": "sessions"}],
        },
        env=VALID_ENV,
        recorded=recorded,
        observed_at=OBSERVED_AT,
    )
    assert result.ok is False
    assert result.data is None
    assert result.evidence is not None
    assert result.evidence["verification_reason"] == "auth_failed"
    assert result.evidence["source"] == "ga4/ga4_run_report"


def test_empty_run_report_maps_to_empty_result_nhv() -> None:
    recorded = {"ga4_run_report": HTTP["empty_run_report"]}
    result = call_tool(
        "ga4_run_report",
        {
            "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-07"}],
            "metrics": [{"name": "sessions"}],
        },
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
            "ga4_run_realtime_report",
            {},
            env=VALID_ENV,
            recorded=HTTP,
            observed_at=OBSERVED_AT,
        )


def test_call_tool_requires_recorded_transport_in_tests() -> None:
    with pytest.raises(ValueError, match="recorded"):
        call_tool(
            "ga4_get_metadata",
            {},
            env=VALID_ENV,
            recorded=None,
            observed_at=OBSERVED_AT,
        )
