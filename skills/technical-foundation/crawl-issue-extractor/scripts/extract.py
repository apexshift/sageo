"""Extract and classify crawl issues from a crawl-log (fixture or connector)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

MAX_REDIRECT_HOPS = 2
CONNECTOR_FAILURE_REASONS = frozenset(
    {
        "missing_credentials",
        "auth_failed",
        "rate_limited",
        "timeout",
        "upstream_error",
        "empty_result",
    }
)


class CrawlSerpError(Exception):
    """Raised by a crawl_serp connector when the fetch cannot complete."""

    def __init__(self, reason: str, message: str | None = None) -> None:
        if reason not in CONNECTOR_FAILURE_REASONS:
            raise ValueError(
                f"unknown crawl_serp failure reason: {reason!r}; "
                f"expected one of {sorted(CONNECTOR_FAILURE_REASONS)}"
            )
        self.reason = reason
        super().__init__(message or reason)


class CrawlSerpConnector(Protocol):
    """Minimal crawl_serp seam used by this Skill (P3 packs implement it)."""

    def fetch_crawl_log(self, job_id: str) -> Mapping[str, Any]:
        """Return a crawl-log map for ``job_id``, or raise ``CrawlSerpError``."""


def extract_crawl_issues(
    crawl_log: Mapping[str, Any] | None = None,
    *,
    source: str,
    observed_at: str | None = None,
    crawl_serp: CrawlSerpConnector | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Classify crawl-log entries into findings + Evidence.

    Hermetic when ``crawl_log`` is supplied. When omitted, loads via
    ``crawl_serp.fetch_crawl_log(job_id)`` (mocked in tests; live pack is P3).
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    via_connector = False

    if crawl_log is None:
        if crawl_serp is None or not job_id:
            raise ValueError(
                "extract_crawl_issues requires crawl_log, or crawl_serp with job_id"
            )
        via_connector = True
        try:
            crawl_log = crawl_serp.fetch_crawl_log(job_id)
        except CrawlSerpError as exc:
            return _connector_failure_result(
                reason=exc.reason,
                source=source,
                observed_at=observed,
            )

    if not isinstance(crawl_log, Mapping):
        if via_connector:
            return _connector_failure_result(
                reason="upstream_error",
                source=source,
                observed_at=observed,
            )
        raise TypeError("crawl_log must be a mapping")

    raw_entries = crawl_log.get("entries", [])
    if not isinstance(raw_entries, list):
        if via_connector:
            return _connector_failure_result(
                reason="upstream_error",
                source=source,
                observed_at=observed,
            )
        raise TypeError("crawl_log entries must be a list")

    if via_connector and len(raw_entries) == 0:
        return _connector_failure_result(
            reason="empty_result",
            source=source,
            observed_at=observed,
        )

    if any(not isinstance(entry, Mapping) for entry in raw_entries):
        if via_connector:
            return _connector_failure_result(
                reason="upstream_error",
                source=source,
                observed_at=observed,
            )
        raise TypeError("crawl_log entries must be mappings")

    entries = list(raw_entries)
    total = len(entries)

    client_errors = [e for e in entries if _is_client_error(e)]
    server_errors = [e for e in entries if _is_server_error(e)]
    long_redirects = [e for e in entries if _is_long_redirect(e)]
    timeouts = [e for e in entries if _error_equals(e, "timeout")]
    soft_404s = [e for e in entries if _error_equals(e, "soft_404")]

    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    _emit_count_finding(
        findings,
        evidence_items,
        finding_id="crawl.client_error",
        matches=client_errors,
        total=total,
        pass_summary="No HTTP 4xx client errors in the crawl log.",
        fail_summary_fmt="Found {n} HTTP 4xx client error(s) in the crawl log.",
        claim_zero=f"0 of {total} crawl entries returned HTTP 4xx.",
        claim_hit_fmt=(
            "{n} of {total} crawl entries returned HTTP 4xx (e.g. {example})."
        ),
        source=source,
        observed_at=observed,
    )
    _emit_count_finding(
        findings,
        evidence_items,
        finding_id="crawl.server_error",
        matches=server_errors,
        total=total,
        pass_summary="No HTTP 5xx server errors in the crawl log.",
        fail_summary_fmt="Found {n} HTTP 5xx server error(s) in the crawl log.",
        claim_zero=f"0 of {total} crawl entries returned HTTP 5xx.",
        claim_hit_fmt=(
            "{n} of {total} crawl entries returned HTTP 5xx (e.g. {example})."
        ),
        source=source,
        observed_at=observed,
    )
    _emit_count_finding(
        findings,
        evidence_items,
        finding_id="crawl.redirect_chain",
        matches=long_redirects,
        total=total,
        pass_summary=(
            f"No redirect chains exceed the maximum hop count (≤{MAX_REDIRECT_HOPS})."
        ),
        fail_summary_fmt=(
            "Found {n} redirect chain(s) exceeding the maximum hop count "
            f"(≤{MAX_REDIRECT_HOPS})."
        ),
        claim_zero=(
            f"0 of {total} crawl entries exceed {MAX_REDIRECT_HOPS} redirect hops."
        ),
        claim_hit_fmt=(
            "{n} of {total} crawl entries exceed "
            f"{MAX_REDIRECT_HOPS} redirect hops (e.g. {{example}})."
        ),
        source=source,
        observed_at=observed,
    )
    _emit_count_finding(
        findings,
        evidence_items,
        finding_id="crawl.timeout",
        matches=timeouts,
        total=total,
        pass_summary="No crawl timeouts in the crawl log.",
        fail_summary_fmt="Found {n} crawl timeout(s) in the crawl log.",
        claim_zero=f"0 of {total} crawl entries timed out.",
        claim_hit_fmt="{n} of {total} crawl entries timed out (e.g. {example}).",
        source=source,
        observed_at=observed,
    )

    if soft_404s:
        n = len(soft_404s)
        example = _entry_url(soft_404s[0])
        findings.append(
            _finding(
                "crawl.soft_404",
                "fail",
                f"Found {n} soft-404 candidate(s) that need human verification.",
            )
        )
        evidence_items.append(
            _evidence(
                f"{n} of {total} crawl entries are soft-404 candidates "
                f"(e.g. {example}).",
                source=source,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Crawl marked the URL as soft_404; confirm whether the "
                    "page is a true not-found experience"
                ),
            )
        )

    return {"findings": findings, "evidence": evidence_items}


def _emit_count_finding(
    findings: list[dict[str, str]],
    evidence_items: list[dict[str, str]],
    *,
    finding_id: str,
    matches: list[Mapping[str, Any]],
    total: int,
    pass_summary: str,
    fail_summary_fmt: str,
    claim_zero: str,
    claim_hit_fmt: str,
    source: str,
    observed_at: str,
) -> None:
    n = len(matches)
    if n == 0:
        findings.append(_finding(finding_id, "pass", pass_summary))
        evidence_items.append(
            _evidence(
                claim_zero,
                source=source,
                observed_at=observed_at,
                confidence="high",
            )
        )
        return

    findings.append(
        _finding(finding_id, "fail", fail_summary_fmt.format(n=n))
    )
    evidence_items.append(
        _evidence(
            claim_hit_fmt.format(n=n, total=total, example=_entry_url(matches[0])),
            source=source,
            observed_at=observed_at,
            confidence="high",
        )
    )


def _connector_failure_result(
    *,
    reason: str,
    source: str,
    observed_at: str,
) -> dict[str, Any]:
    return {
        "findings": [
            _finding(
                "crawl.connector",
                "fail",
                f"crawl_serp connector failed ({reason}).",
            )
        ],
        "evidence": [
            _evidence(
                f"crawl_serp connector could not supply a crawl log ({reason}).",
                source=source,
                observed_at=observed_at,
                confidence="needs_human_verification",
                verification_reason=reason,
            )
        ],
    }


def _is_client_error(entry: Mapping[str, Any]) -> bool:
    status = entry.get("status")
    return isinstance(status, int) and 400 <= status <= 499


def _is_server_error(entry: Mapping[str, Any]) -> bool:
    status = entry.get("status")
    return isinstance(status, int) and 500 <= status <= 599


def _is_long_redirect(entry: Mapping[str, Any]) -> bool:
    count = entry.get("redirect_count", 0)
    return isinstance(count, int) and not isinstance(count, bool) and count > MAX_REDIRECT_HOPS


def _error_equals(entry: Mapping[str, Any], expected: str) -> bool:
    error = entry.get("error")
    return isinstance(error, str) and error.strip().casefold() == expected


def _entry_url(entry: Mapping[str, Any]) -> str:
    url = entry.get("url")
    if isinstance(url, str) and url.strip():
        return url.strip()
    return "unknown"


def _finding(finding_id: str, status: str, summary: str) -> dict[str, str]:
    return {"id": finding_id, "status": status, "summary": summary}


def _evidence(
    claim: str,
    *,
    source: str,
    observed_at: str,
    confidence: str,
    verification_reason: str | None = None,
) -> dict[str, str]:
    item = {
        "claim": claim,
        "source": source,
        "observed_at": observed_at,
        "confidence": confidence,
        "method": "crawl-log-heuristics",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
