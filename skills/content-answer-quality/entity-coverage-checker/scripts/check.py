"""Check topical/entity coverage signals on a page and emit Evidence."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

JSON_LD_SCRIPT_RE = re.compile(
    r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_OR_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

ENTITY_TYPES = frozenset(
    {
        "Organization",
        "Person",
        "Product",
        "Brand",
        "Place",
        "LocalBusiness",
    }
)


def check_entity_coverage(
    html: str,
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Check named schema entities, sameAs, and visible name coverage.

    Hermetic: operates only on the provided HTML string (no network I/O / LLM).
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
        entities.extend(_collect_entities(data))

    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    for _ in range(parse_failures):
        findings.append(
            _finding(
                "entity.jsonld.parse",
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

    named = [e for e in entities if _entity_name(e) is not None]
    if not named:
        if parse_failures and parse_failures == len(blocks) and blocks:
            return {"findings": findings, "evidence": evidence_items}
        findings.append(
            _finding(
                "entity.schema_present",
                "fail",
                "No named schema.org entity (Organization/Person/Product/Brand/Place/LocalBusiness) found.",
            )
        )
        evidence_items.append(
            _evidence(
                "Page does not include a named schema.org coverage entity.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
        return {"findings": findings, "evidence": evidence_items}

    primary = named[0]
    primary_name = _entity_name(primary)
    assert primary_name is not None
    primary_types = _collect_types(primary)
    type_label = ", ".join(t for t in primary_types if t in ENTITY_TYPES) or primary_types[0]

    findings.append(
        _finding(
            "entity.schema_present",
            "pass",
            "Page includes a named schema.org entity.",
        )
    )
    evidence_items.append(
        _evidence(
            f"Page includes schema entity @type {type_label} named '{primary_name}'.",
            source=source,
            observed_at=observed,
            confidence="high",
        )
    )

    same_as = _same_as_links(primary)
    if same_as:
        findings.append(
            _finding(
                "entity.same_as",
                "pass",
                "Primary entity includes sameAs identity links.",
            )
        )
        evidence_items.append(
            _evidence(
                f"{type_label} '{primary_name}' declares {len(same_as)} sameAs "
                "identity link(s).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "entity.same_as",
                "fail",
                "Primary entity is missing sameAs identity links.",
            )
        )
        evidence_items.append(
            _evidence(
                f"{type_label} '{primary_name}' has no sameAs identity links.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    visible = _visible_text(html)
    if primary_name.casefold() in visible.casefold():
        findings.append(
            _finding(
                "entity.visible_mention",
                "pass",
                "Entity name appears in visible page text.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Entity name '{primary_name}' appears in visible page text.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "entity.visible_mention",
                "fail",
                "Entity name does not appear in visible page text.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Entity name '{primary_name}' was not observed in visible page text.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    unique_names = list(
        dict.fromkeys(n for n in (_entity_name(e) for e in named) if n is not None)
    )
    if len(unique_names) > 1:
        findings.append(
            _finding(
                "entity.name_conflict",
                "fail",
                "Conflicting entity name values across schema blocks.",
            )
        )
        evidence_items.append(
            _evidence(
                "Schema entities disagree on name ("
                + " vs ".join(unique_names)
                + ").",
                source=source,
                observed_at=observed,
                confidence="needs_human_verification",
                verification_reason=(
                    "Contradictory entity name values across JSON-LD blocks"
                ),
            )
        )

    return {"findings": findings, "evidence": evidence_items}


def _collect_entities(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        found: list[dict[str, Any]] = []
        for item in data:
            found.extend(_collect_entities(item))
        return found
    if not isinstance(data, dict):
        return []
    if "@graph" in data:
        return _collect_entities(data["@graph"])
    types = _collect_types(data)
    if ENTITY_TYPES.intersection(types):
        return [data]
    return []


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


def _same_as_links(entity: dict[str, Any]) -> list[str]:
    raw = entity.get("sameAs")
    if raw is None:
        return []
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return []


def _visible_text(html: str) -> str:
    without_scripts = SCRIPT_OR_STYLE_RE.sub(" ", html)
    text = TAG_RE.sub(" ", without_scripts)
    return WHITESPACE_RE.sub(" ", text).strip()


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
        "method": "entity-html-parse",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
