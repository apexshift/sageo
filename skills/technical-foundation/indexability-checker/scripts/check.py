"""Assess indexability signals from HTTP status, headers, and HTML."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping

ROBOTS_META_RE = re.compile(
    r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\']([^"\']*)["\']'
    r'|<meta\b[^>]*\bcontent=["\']([^"\']*)["\'][^>]*\bname=["\']robots["\']',
    re.IGNORECASE,
)

BLOCKING_TOKENS = frozenset({"noindex", "none"})


def check_indexability(
    *,
    status: int,
    headers: Mapping[str, str],
    html: str,
    source_response: str,
    source_html: str,
    source_bundle: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Return findings + Evidence for core indexability signals.

    Hermetic: operates only on the provided status, headers, and HTML.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    # --- HTTP status ---
    if status == 200:
        findings.append(
            _finding(
                "indexability.status",
                "pass",
                "HTTP status 200 is eligible for indexing.",
            )
        )
        evidence_items.append(
            _evidence(
                f"HTTP response status is {status}.",
                source=source_response,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "indexability.status",
                "fail",
                f"HTTP status {status} is not eligible for indexing as a primary URL.",
            )
        )
        evidence_items.append(
            _evidence(
                f"HTTP response status is {status}.",
                source=source_response,
                observed_at=observed,
                confidence="high",
            )
        )

    # --- X-Robots-Tag ---
    x_robots_raw = _header_value(headers, "x-robots-tag")
    header_blocks = _directive_blocks(x_robots_raw)
    if x_robots_raw is None:
        findings.append(
            _finding(
                "indexability.x_robots_tag",
                "pass",
                "No X-Robots-Tag noindex/none directive observed.",
            )
        )
        evidence_items.append(
            _evidence(
                "X-Robots-Tag header does not include noindex or none.",
                source=source_response,
                observed_at=observed,
                confidence="high",
            )
        )
    elif header_blocks:
        findings.append(
            _finding(
                "indexability.x_robots_tag",
                "fail",
                "X-Robots-Tag includes noindex or none.",
            )
        )
        evidence_items.append(
            _evidence(
                f"X-Robots-Tag content is '{x_robots_raw}' and blocks indexing.",
                source=source_response,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "indexability.x_robots_tag",
                "pass",
                f"X-Robots-Tag allows indexing ({x_robots_raw}).",
            )
        )
        evidence_items.append(
            _evidence(
                f"X-Robots-Tag content is '{x_robots_raw}' and allows indexing.",
                source=source_response,
                observed_at=observed,
                confidence="high",
            )
        )

    # --- robots meta ---
    robots_meta_raw = _robots_meta_content(html)
    meta_blocks = _directive_blocks(robots_meta_raw)
    if robots_meta_raw is None:
        findings.append(
            _finding(
                "indexability.robots_meta",
                "pass",
                "No robots meta noindex/none directive observed.",
            )
        )
        evidence_items.append(
            _evidence(
                "Robots meta does not include noindex or none.",
                source=source_html,
                observed_at=observed,
                confidence="high",
            )
        )
    elif meta_blocks:
        findings.append(
            _finding(
                "indexability.robots_meta",
                "fail",
                "Robots meta includes noindex or none.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Robots meta content is '{robots_meta_raw}' and blocks indexing.",
                source=source_html,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "indexability.robots_meta",
                "pass",
                f"Robots meta allows indexing ({robots_meta_raw}).",
            )
        )
        evidence_items.append(
            _evidence(
                f"Robots meta content is '{robots_meta_raw}' and allows indexing.",
                source=source_html,
                observed_at=observed,
                confidence="high",
            )
        )

    # --- Conflict when both signals are present and disagree ---
    if x_robots_raw is not None and robots_meta_raw is not None and header_blocks != meta_blocks:
        findings.append(
            _finding(
                "indexability.signal_conflict",
                "fail",
                "X-Robots-Tag and robots meta disagree on indexability.",
            )
        )
        if header_blocks and not meta_blocks:
            claim = (
                "X-Robots-Tag blocks indexing while robots meta allows indexing."
            )
        else:
            claim = (
                "X-Robots-Tag allows indexing while robots meta blocks indexing."
            )
        evidence_items.append(
            _evidence(
                claim,
                source=source_bundle,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Header and meta robots directives disagree on whether "
                    "the URL may be indexed"
                ),
            )
        )

    return {"findings": findings, "evidence": evidence_items}


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
        "method": "headers-html-parse",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            text = value.strip()
            return text if text else None
    return None


def _robots_meta_content(html: str) -> str | None:
    match = ROBOTS_META_RE.search(html)
    if match is None:
        return None
    content = match.group(1) if match.group(1) is not None else match.group(2)
    if content is None:
        return None
    text = content.strip()
    return text if text else None


def _directive_blocks(content: str | None) -> bool:
    if content is None:
        return False
    tokens = {token.strip().lower() for token in content.split(",") if token.strip()}
    return bool(tokens & BLOCKING_TOKENS)
