"""Unit seam: extract_crawl_issues with crawl_serp connector mocked."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from sageo.testing import golden as skill_golden

SKILL_ROOT = (
    Path(__file__).resolve().parents[5]
    / "skills"
    / "technical-foundation"
    / "crawl-issue-extractor"
)
EXTRACT_SCRIPT = SKILL_ROOT / "scripts" / "extract.py"
FIXTURE_HAPPY = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "happy"
    / "input"
    / "crawl_log.json"
)


class _FakeCrawlSerp:
    def __init__(self, result: Mapping[str, Any] | BaseException) -> None:
        self._result = result
        self.calls: list[str] = []

    def fetch_crawl_log(self, job_id: str) -> Mapping[str, Any]:
        self.calls.append(job_id)
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


@pytest.fixture(scope="module")
def extract_mod():
    return skill_golden.load_skill_module(
        EXTRACT_SCRIPT, "crawl_issue_extractor_extract_unit"
    )


def test_loads_crawl_log_via_mocked_connector(extract_mod) -> None:
    import json

    crawl_log = json.loads(FIXTURE_HAPPY.read_text(encoding="utf-8"))
    connector = _FakeCrawlSerp(crawl_log)

    result = extract_mod.extract_crawl_issues(
        source="connector:job-1",
        observed_at="2026-10-27T12:00:00Z",
        crawl_serp=connector,
        job_id="job-1",
    )

    assert connector.calls == ["job-1"]
    assert result["findings"][0]["id"] == "crawl.client_error"
    assert result["findings"][0]["status"] == "pass"
    assert all(item["confidence"] == "high" for item in result["evidence"])


def test_connector_failure_emits_nhv_evidence(extract_mod) -> None:
    connector = _FakeCrawlSerp(
        extract_mod.CrawlSerpError("rate_limited", "upstream 429")
    )

    result = extract_mod.extract_crawl_issues(
        source="connector:job-429",
        observed_at="2026-10-27T12:00:00Z",
        crawl_serp=connector,
        job_id="job-429",
    )

    assert result["findings"] == [
        {
            "id": "crawl.connector",
            "status": "fail",
            "summary": "crawl_serp connector failed (rate_limited).",
        }
    ]
    assert result["evidence"] == [
        {
            "claim": (
                "crawl_serp connector could not supply a crawl log (rate_limited)."
            ),
            "source": "connector:job-429",
            "observed_at": "2026-10-27T12:00:00Z",
            "confidence": "needs_human_verification",
            "verification_reason": "rate_limited",
            "method": "crawl-log-heuristics",
        }
    ]


def test_empty_crawl_log_passes_all_categories(extract_mod) -> None:
    result = extract_mod.extract_crawl_issues(
        {"entries": []},
        source="fixture:empty",
        observed_at="2026-10-27T12:00:00Z",
    )

    assert [f["id"] for f in result["findings"]] == [
        "crawl.client_error",
        "crawl.server_error",
        "crawl.redirect_chain",
        "crawl.timeout",
    ]
    assert all(f["status"] == "pass" for f in result["findings"])
    assert all(item["confidence"] == "high" for item in result["evidence"])


def test_connector_empty_result_emits_nhv(extract_mod) -> None:
    connector = _FakeCrawlSerp(extract_mod.CrawlSerpError("empty_result"))

    result = extract_mod.extract_crawl_issues(
        source="connector:job-empty",
        observed_at="2026-10-27T12:00:00Z",
        crawl_serp=connector,
        job_id="job-empty",
    )

    assert result["findings"][0]["id"] == "crawl.connector"
    assert result["evidence"][0]["verification_reason"] == "empty_result"
    assert result["evidence"][0]["confidence"] == "needs_human_verification"


def test_connector_returned_empty_log_emits_nhv(extract_mod) -> None:
    connector = _FakeCrawlSerp({"entries": []})

    result = extract_mod.extract_crawl_issues(
        source="connector:job-blank",
        observed_at="2026-10-27T12:00:00Z",
        crawl_serp=connector,
        job_id="job-blank",
    )

    assert result["findings"][0]["id"] == "crawl.connector"
    assert result["evidence"][0]["verification_reason"] == "empty_result"


def test_requires_crawl_log_or_connector(extract_mod) -> None:
    with pytest.raises(ValueError, match="crawl_log"):
        extract_mod.extract_crawl_issues(source="missing")
