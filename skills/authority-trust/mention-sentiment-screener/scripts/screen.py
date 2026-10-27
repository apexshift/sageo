"""Screen brand mentions for sentiment/risk and emit Evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def screen_mention_sentiment(
    corpus: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Classify opportunity-corpus mentions for sentiment and reputation risk.

    Hermetic: operates only on the provided corpus map (no network I/O).
    Findings-only; does not propose outreach, suppression, or live-site changes.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    brand = corpus.get("brand")
    if not isinstance(brand, str) or not brand.strip():
        raise ValueError("opportunity corpus requires a non-empty brand string")
    brand = brand.strip()

    raw_candidates = corpus.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise TypeError("opportunity corpus candidates must be a list")

    clear: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for candidate in raw_candidates:
        if not isinstance(candidate, dict):
            continue
        classification = _classify_candidate(candidate)
        if classification == "clear":
            clear.append(candidate)
        elif classification == "risk":
            risks.append(candidate)
        elif classification == "conflict":
            conflicts.append(candidate)

    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    if clear:
        count = len(clear)
        summary = (
            f"Found {count} clear positive/neutral brand mention."
            if count == 1
            else f"Found {count} clear positive/neutral brand mentions."
        )
        findings.append(_finding("mention.sentiment_ok", "pass", summary))
        for candidate in clear:
            evidence_items.append(
                _evidence(
                    _clear_claim(candidate, brand),
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
        findings.append(
            _finding(
                "mention.low_risk",
                "pass",
                "Screened mentions show no declared risk signals.",
            )
        )
        evidence_items.append(
            _evidence(
                f"{count} candidate(s) cleared sentiment/risk screening for {brand}.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "mention.sentiment_ok",
                "fail",
                "No clear positive/neutral brand mentions found in the corpus.",
            )
        )
        evidence_items.append(
            _evidence(
                f"No candidates for {brand} met clear sentiment screening criteria "
                "(brand mention with positive/neutral sentiment and no risk signals).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if risks:
        findings.append(
            _finding(
                "mention.risk_detected",
                "fail",
                "Some brand mentions carry negative sentiment or risk signals.",
            )
        )
        for candidate in risks:
            cand_id = str(candidate.get("id", "unknown"))
            title = str(candidate.get("title", "")).strip() or cand_id
            evidence_items.append(
                _evidence(
                    f"Candidate '{cand_id}' ({title}) flags sentiment/risk for {brand}.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )

    if conflicts:
        findings.append(
            _finding(
                "mention.signal_conflict",
                "fail",
                "Some mentions mix sentiment cues with risk signals or are marked mixed.",
            )
        )
        for candidate in conflicts:
            cand_id = str(candidate.get("id", "unknown"))
            title = str(candidate.get("title", "")).strip() or cand_id
            evidence_items.append(
                _evidence(
                    f"Candidate '{cand_id}' ({title}) has conflicting sentiment/risk "
                    "signals.",
                    source=source,
                    observed_at=observed,
                    confidence="needs_human_verification",
                    verification_reason=(
                        "Mention shows mixed sentiment or combines safe sentiment "
                        "cues with risk signals"
                    ),
                )
            )

    return {"findings": findings, "evidence": evidence_items}


def _classify_candidate(candidate: Mapping[str, Any]) -> str:
    if not bool(candidate.get("mentions_brand")):
        return "rejected"

    sentiment = _sentiment(candidate)
    risk = _risk_signals(candidate)
    safe_cue = sentiment in {"positive", "neutral"}
    risk_cue = sentiment == "negative" or bool(risk)
    mixed = sentiment == "mixed"

    if mixed or (safe_cue and risk_cue):
        return "conflict"
    if safe_cue and not risk_cue:
        return "clear"
    if risk_cue:
        return "risk"
    return "rejected"


def _sentiment(candidate: Mapping[str, Any]) -> str:
    raw = candidate.get("sentiment")
    if not isinstance(raw, str):
        return ""
    return raw.strip().lower()


def _risk_signals(candidate: Mapping[str, Any]) -> list[str]:
    raw = candidate.get("risk_signals", [])
    if not isinstance(raw, list):
        return []
    return [str(item).strip().lower() for item in raw if str(item).strip()]


def _clear_claim(candidate: Mapping[str, Any], brand: str) -> str:
    cand_id = str(candidate.get("id", "unknown"))
    title = str(candidate.get("title", "")).strip() or cand_id
    sentiment = _sentiment(candidate) or "neutral"
    return (
        f"Candidate '{cand_id}' ({title}) mentions {brand} with {sentiment} "
        "sentiment and no risk signals."
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
        "method": "mention-sentiment-heuristics",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
