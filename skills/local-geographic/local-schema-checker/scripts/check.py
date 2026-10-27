"""Validate LocalBusiness structured data on a page and emit Evidence."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

JSON_LD_SCRIPT_RE = re.compile(
    r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def check_local_schema(
    html: str,
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Validate LocalBusiness JSON-LD on ``html``; return findings + Evidence.

    Hermetic: operates only on the provided HTML string (no network I/O).
    Complements page-generic ``schema-validator`` by focusing on local fields.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    blocks = [m.group(1).strip() for m in JSON_LD_SCRIPT_RE.finditer(html)]
    entities: list[dict[str, Any]] = []
    parse_failures = 0

    for raw in blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            parse_failures += 1
            continue
        entities.extend(_collect_local_business(data))

    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    for _ in range(parse_failures):
        findings.append(
            _finding(
                "local_schema.jsonld.parse",
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

    if not entities:
        if parse_failures and parse_failures == len(blocks):
            return {"findings": findings, "evidence": evidence_items}
        findings.append(
            _finding(
                "local_schema.present",
                "fail",
                "No LocalBusiness structured data found on the page.",
            )
        )
        evidence_items.append(
            _evidence(
                "Page does not include JSON-LD with @type LocalBusiness.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
        return {"findings": findings, "evidence": evidence_items}

    primary = entities[0]
    findings.append(
        _finding(
            "local_schema.present",
            "pass",
            "Found LocalBusiness structured data on the page.",
        )
    )
    evidence_items.append(
        _evidence(
            "Page includes JSON-LD with @type LocalBusiness.",
            source=source,
            observed_at=observed,
            confidence="high",
        )
    )

    name = _entity_name(primary)
    if name is not None:
        findings.append(
            _finding("local_schema.name", "pass", "LocalBusiness name is present.")
        )
        evidence_items.append(
            _evidence(
                f"LocalBusiness name is '{name}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "local_schema.name",
                "fail",
                "LocalBusiness name is missing.",
            )
        )
        evidence_items.append(
            _evidence(
                "LocalBusiness JSON-LD is present but name is missing.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    street, locality = _address_parts(primary)
    if street is not None and locality is not None:
        findings.append(
            _finding(
                "local_schema.address",
                "pass",
                "LocalBusiness address includes streetAddress and addressLocality.",
            )
        )
        evidence_items.append(
            _evidence(
                f"LocalBusiness address includes streetAddress '{street}' "
                f"and addressLocality '{locality}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "local_schema.address",
                "fail",
                "LocalBusiness address is missing streetAddress or addressLocality.",
            )
        )
        evidence_items.append(
            _evidence(
                "LocalBusiness address lacks streetAddress and/or addressLocality.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    telephone = _entity_telephone(primary)
    if telephone is not None:
        findings.append(
            _finding(
                "local_schema.telephone",
                "pass",
                "LocalBusiness telephone is present.",
            )
        )
        evidence_items.append(
            _evidence(
                f"LocalBusiness telephone is '{telephone}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "local_schema.telephone",
                "fail",
                "LocalBusiness telephone is missing.",
            )
        )
        evidence_items.append(
            _evidence(
                "LocalBusiness JSON-LD is present but telephone is missing.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    conflict = _nap_conflict(entities)
    if conflict is not None:
        findings.append(
            _finding(
                "local_schema.nap_conflict",
                "fail",
                "Conflicting LocalBusiness name, telephone, or address values.",
            )
        )
        evidence_items.append(
            _evidence(
                conflict,
                source=source,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Contradictory LocalBusiness NAP fields across JSON-LD blocks"
                ),
            )
        )

    return {"findings": findings, "evidence": evidence_items}


def _collect_local_business(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        found: list[dict[str, Any]] = []
        for item in data:
            found.extend(_collect_local_business(item))
        return found
    if not isinstance(data, dict):
        return []
    if "@graph" in data:
        return _collect_local_business(data["@graph"])
    if _is_local_business(data):
        return [data]
    return []


def _is_local_business(entity: dict[str, Any]) -> bool:
    types = _collect_types(entity)
    return "LocalBusiness" in types


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


def _entity_name(entity: dict[str, Any]) -> str | None:
    name = entity.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _entity_telephone(entity: dict[str, Any]) -> str | None:
    telephone = entity.get("telephone")
    if isinstance(telephone, str) and telephone.strip():
        return telephone.strip()
    return None


def _address_parts(entity: dict[str, Any]) -> tuple[str | None, str | None]:
    address = entity.get("address")
    if not isinstance(address, dict):
        return None, None
    street = address.get("streetAddress")
    locality = address.get("addressLocality")
    street_text = street.strip() if isinstance(street, str) and street.strip() else None
    locality_text = (
        locality.strip() if isinstance(locality, str) and locality.strip() else None
    )
    return street_text, locality_text


def _nap_conflict(entities: list[dict[str, Any]]) -> str | None:
    if len(entities) < 2:
        return None

    names = [_entity_name(e) for e in entities]
    phones = [_entity_telephone(e) for e in entities]
    streets = [_address_parts(e)[0] for e in entities]

    unique_names = list(dict.fromkeys(n for n in names if n is not None))
    unique_phones = list(dict.fromkeys(p for p in phones if p is not None))
    unique_streets = list(dict.fromkeys(s for s in streets if s is not None))

    parts: list[str] = []
    if len(unique_names) > 1:
        parts.append(f"name ({' vs '.join(unique_names)})")
    if len(unique_phones) > 1:
        parts.append(f"telephone ({' vs '.join(unique_phones)})")
    if len(unique_streets) > 1:
        parts.append(f"streetAddress ({' vs '.join(unique_streets)})")
    if not parts:
        return None
    return "LocalBusiness blocks disagree on " + ", ".join(parts) + "."


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
        "method": "local-jsonld-parse",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
