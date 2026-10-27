"""Validate JSON-LD structured data on a page and emit Evidence."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

JSON_LD_SCRIPT_RE = re.compile(
    r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def validate_page(
    html: str,
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Validate JSON-LD on ``html`` and return findings plus Evidence.

    Hermetic: operates only on the provided HTML string (no network I/O).
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    blocks = [m.group(1).strip() for m in JSON_LD_SCRIPT_RE.finditer(html)]

    if not blocks:
        return {
            "findings": [
                _finding(
                    "schema.jsonld.absent",
                    "fail",
                    "No application/ld+json blocks found on the page.",
                )
            ],
            "evidence": [
                _evidence(
                    "Page does not include JSON-LD structured data.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            ],
        }

    findings: list[dict[str, Any]] = []
    evidence_items: list[dict[str, Any]] = []
    org_names: list[str] = []

    for raw in blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            findings.append(
                _finding(
                    "schema.jsonld.parse",
                    "fail",
                    "JSON-LD block could not be parsed as JSON.",
                )
            )
            evidence_items.append(
                _evidence(
                    "A JSON-LD script was present but could not be parsed as JSON.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
            continue

        types = _collect_types(data)
        type_label = ", ".join(types) if types else "(missing @type)"
        if types:
            findings.append(
                _finding(
                    "schema.jsonld.valid",
                    "pass",
                    f"Found 1 valid JSON-LD block with @type {type_label}.",
                )
            )
            evidence_items.append(
                _evidence(
                    "Page includes valid JSON-LD structured data with "
                    f"@type {type_label}.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
            if "Organization" in types:
                name = _entity_name(data)
                if name is not None:
                    org_names.append(name)
        else:
            findings.append(
                _finding(
                    "schema.jsonld.type",
                    "fail",
                    "JSON-LD parsed but @type is missing.",
                )
            )
            evidence_items.append(
                _evidence(
                    "JSON-LD is present and parseable but @type is missing.",
                    source=source,
                    observed_at=observed,
                    confidence="medium",
                )
            )

    unique_org_names = list(dict.fromkeys(org_names))
    if len(unique_org_names) > 1:
        joined = " vs ".join(unique_org_names)
        findings.append(
            _finding(
                "schema.jsonld.contradiction",
                "fail",
                "Conflicting Organization name values across JSON-LD blocks.",
            )
        )
        evidence_items.append(
            _evidence(
                f"JSON-LD Organization blocks disagree on name ({joined}).",
                source=source,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Contradictory Organization name values across JSON-LD blocks"
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
        "method": "jsonld-parse",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item


def _collect_types(data: Any) -> list[str]:
    if isinstance(data, list):
        types: list[str] = []
        for item in data:
            types.extend(_collect_types(item))
        return types
    if not isinstance(data, dict):
        return []
    raw = data.get("@type")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t) for t in raw]
    return [str(raw)]


def _entity_name(data: Any) -> str | None:
    if isinstance(data, list):
        for item in data:
            name = _entity_name(item)
            if name is not None:
                return name
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None
