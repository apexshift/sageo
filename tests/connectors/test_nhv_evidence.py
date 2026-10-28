"""Connector NHV Evidence seam: pack + tool + reason → Evidence shape."""

from __future__ import annotations

import pytest

from sageo.connectors.nhv import VERIFICATION_REASONS, nhv_evidence


def test_nhv_evidence_maps_locked_reason_to_evidence_shape() -> None:
    evidence = nhv_evidence(
        pack="gsc",
        tool="gsc_search_analytics_query",
        verification_reason="rate_limited",
        claim="Search Analytics query could not be completed",
        observed_at="2026-10-28T12:00:00+00:00",
    )

    assert evidence == {
        "claim": "Search Analytics query could not be completed",
        "source": "gsc/gsc_search_analytics_query",
        "observed_at": "2026-10-28T12:00:00+00:00",
        "confidence": "needs_human_verification",
        "verification_reason": "rate_limited",
    }


@pytest.mark.parametrize("reason", sorted(VERIFICATION_REASONS))
def test_nhv_evidence_accepts_each_locked_verification_reason(reason: str) -> None:
    evidence = nhv_evidence(
        pack="ga4",
        tool="ga4_run_report",
        verification_reason=reason,
        claim=f"GA4 failure: {reason}",
        observed_at="2026-10-28T12:00:00+00:00",
    )
    assert evidence["verification_reason"] == reason
    assert evidence["confidence"] == "needs_human_verification"
    assert evidence["source"] == "ga4/ga4_run_report"


def test_nhv_evidence_rejects_unknown_verification_reason() -> None:
    with pytest.raises(ValueError, match="verification_reason"):
        nhv_evidence(
            pack="crawl-serp",
            tool="serp_google_organic",
            verification_reason="invented_reason",
            claim="should not build",
            observed_at="2026-10-28T12:00:00+00:00",
        )
