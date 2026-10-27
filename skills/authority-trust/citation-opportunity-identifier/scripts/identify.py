"""Identify white-hat citation opportunities from a corpus and emit Evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def identify_citation_opportunities(
    corpus: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Score opportunity-corpus candidates for white-hat citation opportunities.

    Hermetic: operates only on the provided corpus map (no network I/O).
    Rejects paid placements and declared spam signals; never recommends link buying.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    brand = corpus.get("brand")
    if not isinstance(brand, str) or not brand.strip():
        raise ValueError("opportunity corpus requires a non-empty brand string")
    brand = brand.strip()

    raw_candidates = corpus.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise TypeError("opportunity corpus candidates must be a list")

    opportunities: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for candidate in raw_candidates:
        if not isinstance(candidate, dict):
            continue
        classification = _classify_candidate(candidate)
        if classification == "opportunity":
            opportunities.append(candidate)
        elif classification == "conflict":
            conflicts.append(candidate)

    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    if opportunities:
        count = len(opportunities)
        summary = (
            f"Found {count} white-hat citation opportunity."
            if count == 1
            else f"Found {count} white-hat citation opportunities."
        )
        findings.append(_finding("citation.opportunity_found", "pass", summary))
        for candidate in opportunities:
            evidence_items.append(
                _evidence(
                    _opportunity_claim(candidate, brand),
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
        findings.append(
            _finding(
                "citation.white_hat",
                "pass",
                "Identified opportunities exclude paid placements and spam signals.",
            )
        )
        evidence_items.append(
            _evidence(
                f"{count} candidate(s) qualify as white-hat citation opportunities "
                f"for {brand}.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "citation.opportunity_found",
                "fail",
                "No white-hat citation opportunities found in the corpus.",
            )
        )
        evidence_items.append(
            _evidence(
                f"No candidates for {brand} met white-hat opportunity criteria "
                "(brand mention, non-paid, no spam signals).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if conflicts:
        findings.append(
            _finding(
                "citation.signal_conflict",
                "fail",
                "Some candidates mix opportunity cues with paid/spam risk signals.",
            )
        )
        for candidate in conflicts:
            cand_id = str(candidate.get("id", "unknown"))
            title = str(candidate.get("title", "")).strip() or cand_id
            evidence_items.append(
                _evidence(
                    f"Candidate '{cand_id}' ({title}) has conflicting white-hat "
                    "and risk signals.",
                    source=source,
                    observed_at=observed,
                    confidence="needs_human_verification",
                    verification_reason=(
                        "Candidate shows brand/topical opportunity cues alongside "
                        "paid placement or spam signals"
                    ),
                )
            )

    return {"findings": findings, "evidence": evidence_items}


def _classify_candidate(candidate: Mapping[str, Any]) -> str:
    mentions = bool(candidate.get("mentions_brand"))
    topical = bool(candidate.get("topical_relevance"))
    paid = bool(candidate.get("paid_placement"))
    spam = _spam_signals(candidate)
    opportunity_cue = mentions or topical
    risk_cue = paid or bool(spam)

    if opportunity_cue and risk_cue:
        return "conflict"
    if opportunity_cue and not risk_cue and _has_http_url(candidate):
        return "opportunity"
    return "rejected"


def _spam_signals(candidate: Mapping[str, Any]) -> list[str]:
    raw = candidate.get("spam_signals", [])
    if not isinstance(raw, list):
        return []
    return [str(item).strip().lower() for item in raw if str(item).strip()]


def _has_http_url(candidate: Mapping[str, Any]) -> bool:
    url = candidate.get("url")
    if not isinstance(url, str):
        return False
    return url.startswith("http://") or url.startswith("https://")


def _opportunity_claim(candidate: Mapping[str, Any], brand: str) -> str:
    cand_id = str(candidate.get("id", "unknown"))
    title = str(candidate.get("title", "")).strip() or cand_id
    if candidate.get("mentions_brand"):
        return (
            f"Candidate '{cand_id}' ({title}) mentions {brand} without paid/spam flags."
        )
    return (
        f"Candidate '{cand_id}' ({title}) is topically relevant to {brand} "
        "without paid/spam flags."
    )


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
        "method": "opportunity-corpus-heuristics",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
