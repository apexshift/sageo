"""Score Core Web Vitals lab metrics against good thresholds and emit Evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

# web.dev / CrUX "good" thresholds (lab fixtures use the same numeric bars).
LCP_GOOD_MS = 2500
INP_GOOD_MS = 200
CLS_GOOD = 0.1


def score_cwv(
    metrics: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
    alternate_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Score lab LCP/INP/CLS against good thresholds; return findings + Evidence.

    Hermetic: operates only on the provided metric maps (no network I/O).
    Lab Evidence is labelled via method ``lab-metrics-threshold``.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    lcp_ms = _require_number(metrics, "lcp_ms")
    inp_ms = _require_number(metrics, "inp_ms")
    cls = _require_number(metrics, "cls")

    _score_metric(
        findings,
        evidence_items,
        finding_id="cwv.lcp",
        label="LCP",
        value=lcp_ms,
        unit="ms",
        threshold=LCP_GOOD_MS,
        source=source,
        observed_at=observed,
    )
    _score_metric(
        findings,
        evidence_items,
        finding_id="cwv.inp",
        label="INP",
        value=inp_ms,
        unit="ms",
        threshold=INP_GOOD_MS,
        source=source,
        observed_at=observed,
    )
    _score_metric(
        findings,
        evidence_items,
        finding_id="cwv.cls",
        label="CLS",
        value=cls,
        unit="",
        threshold=CLS_GOOD,
        source=source,
        observed_at=observed,
    )

    if alternate_metrics is not None:
        alt_lcp = _require_number(alternate_metrics, "lcp_ms")
        alt_inp = _require_number(alternate_metrics, "inp_ms")
        alt_cls = _require_number(alternate_metrics, "cls")
        disagreements: list[str] = []
        if _passes(lcp_ms, LCP_GOOD_MS) != _passes(alt_lcp, LCP_GOOD_MS):
            disagreements.append("LCP")
        if _passes(inp_ms, INP_GOOD_MS) != _passes(alt_inp, INP_GOOD_MS):
            disagreements.append("INP")
        if _passes(cls, CLS_GOOD) != _passes(alt_cls, CLS_GOOD):
            disagreements.append("CLS")
        if disagreements:
            joined = ", ".join(disagreements)
            findings.append(
                _finding(
                    "cwv.metric_conflict",
                    "fail",
                    f"Primary and alternate lab metrics disagree on {joined} pass/fail.",
                )
            )
            evidence_items.append(
                _evidence(
                    f"Primary and alternate lab captures disagree on pass/fail "
                    f"for {joined}.",
                    source=source,
                    observed_at=observed,
                    confidence="needs_human_verification",
                    verification_reason=(
                        "Two lab metric captures disagree on Core Web Vitals "
                        "pass/fail for the same URL"
                    ),
                )
            )

    return {"findings": findings, "evidence": evidence_items}


def _score_metric(
    findings: list[dict[str, str]],
    evidence_items: list[dict[str, str]],
    *,
    finding_id: str,
    label: str,
    value: float,
    unit: str,
    threshold: float,
    source: str,
    observed_at: str,
) -> None:
    value_text = _format_value(value, unit)
    threshold_text = _format_value(threshold, unit)
    if _passes(value, threshold):
        findings.append(
            _finding(
                finding_id,
                "pass",
                f"{label} {value_text} is within the lab good threshold (≤{threshold_text}).",
            )
        )
    else:
        findings.append(
            _finding(
                finding_id,
                "fail",
                f"{label} {value_text} exceeds the lab good threshold (≤{threshold_text}).",
            )
        )
    evidence_items.append(
        _evidence(
            f"Lab {label} is {value_text} (good threshold ≤{threshold_text}).",
            source=source,
            observed_at=observed_at,
            confidence="high",
        )
    )


def _passes(value: float, threshold: float) -> bool:
    return value <= threshold


def _format_value(value: float, unit: str) -> str:
    if unit == "ms":
        if float(value).is_integer():
            return f"{int(value)}ms"
        return f"{value}ms"
    # CLS is unitless; keep compact decimal without trailing noise.
    text = f"{value:g}"
    return text


def _require_number(metrics: Mapping[str, Any], key: str) -> float:
    if key not in metrics:
        raise KeyError(f"lab metrics missing required key: {key}")
    raw = metrics[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise TypeError(f"lab metrics {key} must be a number, got {type(raw).__name__}")
    return float(raw)


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
        "method": "lab-metrics-threshold",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
