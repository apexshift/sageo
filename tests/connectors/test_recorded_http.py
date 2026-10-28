"""Recorded-HTTP fixture loader seam for hermetic Connector tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from sageo.testing.recorded_http import RecordedExchange, load_recorded_http

FIXTURES = Path(__file__).parent / "fixtures" / "sample-http"


def test_load_recorded_http_loads_request_response_pairs() -> None:
    exchanges = load_recorded_http(FIXTURES)

    assert set(exchanges) == {"search_analytics", "auth_failed"}
    search = exchanges["search_analytics"]
    assert isinstance(search, RecordedExchange)
    assert search.request["method"] == "POST"
    assert search.request["url"].endswith("/searchAnalytics/query")
    assert search.response["status"] == 200
    assert search.response["body"]["rows"][0]["clicks"] == 12


def test_load_recorded_http_preserves_error_status_bodies() -> None:
    exchanges = load_recorded_http(FIXTURES)
    auth = exchanges["auth_failed"]
    assert auth.response["status"] == 401
    assert auth.response["body"]["error"]["message"] == "Unauthorized"


def test_load_recorded_http_rejects_missing_directory() -> None:
    with pytest.raises(FileNotFoundError, match="recorded HTTP"):
        load_recorded_http(FIXTURES / "does-not-exist")


def test_load_recorded_http_rejects_exchange_missing_request_or_response(
    tmp_path: Path,
) -> None:
    bad = tmp_path / "http"
    bad.mkdir()
    (bad / "broken.json").write_text('{"request": {"method": "GET"}}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="request.*response"):
        load_recorded_http(bad)
