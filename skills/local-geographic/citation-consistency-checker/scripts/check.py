"""Check NAP/citation consistency across directory listings and emit Evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


NAP_FIELDS = ("name", "streetAddress", "addressLocality", "telephone")


def check_citation_consistency(
    listings_nap: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Compare directory listings to a canonical NAP; return findings + Evidence.

    Hermetic: operates only on the provided listings-nap map (no network I/O).
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    canonical = listings_nap.get("canonical")
    if not isinstance(canonical, Mapping):
        raise TypeError("listings-nap requires a canonical NAP map")
    _require_canonical(canonical)
    brand = str(canonical["name"]).strip()

    raw_listings = listings_nap.get("listings", [])
    if not isinstance(raw_listings, list):
        raise TypeError("listings-nap listings must be a list")

    consistent: list[dict[str, Any]] = []
    mismatches: list[tuple[dict[str, Any], list[str]]] = []
    conflicts: list[dict[str, Any]] = []
    incompletes: list[dict[str, Any]] = []

    for listing in raw_listings:
        if not isinstance(listing, dict):
            continue
        classification, details = _classify_listing(listing, canonical)
        if classification == "consistent":
            consistent.append(listing)
        elif classification == "mismatch":
            mismatches.append((listing, details))
        elif classification == "conflict":
            conflicts.append(listing)
        elif classification == "incomplete":
            incompletes.append(listing)

    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    if not raw_listings:
        findings.append(
            _finding(
                "citation.nap_consistent",
                "fail",
                "No listings available to compare against the canonical NAP.",
            )
        )
        evidence_items.append(
            _evidence(
                f"No directory listings were provided to check NAP consistency "
                f"for {brand}.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
        return {"findings": findings, "evidence": evidence_items}

    if consistent and not mismatches and not conflicts and not incompletes:
        count = len(consistent)
        findings.append(
            _finding(
                "citation.nap_consistent",
                "pass",
                f"All {count} listings match the canonical NAP.",
            )
        )
        for listing in consistent:
            evidence_items.append(
                _evidence(
                    _listing_match_claim(listing, brand),
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
        evidence_items.append(
            _evidence(
                f"{count} listing(s) are consistent with the canonical NAP "
                f"for {brand}.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
        return {"findings": findings, "evidence": evidence_items}

    findings.append(
        _finding(
            "citation.nap_consistent",
            "fail",
            "NAP consistency failed across directory listings.",
        )
    )
    evidence_items.append(
        _evidence(
            f"No listings fully matched the canonical NAP for {brand}."
            if not consistent
            else (
                f"Only {len(consistent)} of {len(raw_listings)} listing(s) matched "
                f"the canonical NAP for {brand}."
            ),
            source=source,
            observed_at=observed,
            confidence="high",
        )
    )

    if mismatches:
        findings.append(
            _finding(
                "citation.nap_mismatch",
                "fail",
                "Some listings disagree with the canonical NAP.",
            )
        )
        for listing, fields in mismatches:
            listing_id = str(listing.get("id", "unknown"))
            directory = str(listing.get("directory", "")).strip() or listing_id
            field_list = ", ".join(fields)
            evidence_items.append(
                _evidence(
                    f"Listing '{listing_id}' ({directory}) mismatches canonical NAP "
                    f"({field_list}).",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )

    if incompletes:
        findings.append(
            _finding(
                "citation.listing_incomplete",
                "fail",
                "Some listings are missing NAP fields needed for comparison.",
            )
        )
        for listing in incompletes:
            listing_id = str(listing.get("id", "unknown"))
            directory = str(listing.get("directory", "")).strip() or listing_id
            evidence_items.append(
                _evidence(
                    f"Listing '{listing_id}' ({directory}) is missing one or more "
                    "NAP fields.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )

    if conflicts:
        findings.append(
            _finding(
                "citation.nap_conflict",
                "fail",
                "Some listings have near-variant NAP values that need human "
                "verification.",
            )
        )
        for listing in conflicts:
            listing_id = str(listing.get("id", "unknown"))
            directory = str(listing.get("directory", "")).strip() or listing_id
            evidence_items.append(
                _evidence(
                    f"Listing '{listing_id}' ({directory}) has near-variant NAP "
                    "fields versus canonical.",
                    source=source,
                    observed_at=observed,
                    confidence="needs_human_verification",
                    verification_reason=(
                        "Listing NAP overlaps canonical values as a near-variant "
                        "(substring) rather than an exact match"
                    ),
                )
            )

    return {"findings": findings, "evidence": evidence_items}


def _require_canonical(canonical: Mapping[str, Any]) -> None:
    for field in NAP_FIELDS:
        value = canonical.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"canonical NAP requires non-empty {field}")


def _classify_listing(
    listing: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> tuple[str, list[str]]:
    relations = {
        field: _field_relation(listing.get(field), canonical[field], phone=field == "telephone")
        for field in NAP_FIELDS
    }
    if any(rel == "ambiguous" for rel in relations.values()):
        return "conflict", []
    mismatch_fields = [field for field, rel in relations.items() if rel == "mismatch"]
    if mismatch_fields:
        return "mismatch", mismatch_fields
    if any(rel == "missing" for rel in relations.values()):
        return "incomplete", []
    return "consistent", []


def _field_relation(listing_value: Any, canonical_value: str, *, phone: bool) -> str:
    if not isinstance(listing_value, str) or not listing_value.strip():
        return "missing"
    if phone:
        left = _normalize_phone(listing_value)
        right = _normalize_phone(canonical_value)
        if left == right:
            return "match"
        return "mismatch"
    left = _normalize_text(listing_value)
    right = _normalize_text(canonical_value)
    if left == right:
        return "match"
    if left in right or right in left:
        return "ambiguous"
    return "mismatch"


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return digits


def _listing_match_claim(listing: Mapping[str, Any], brand: str) -> str:
    listing_id = str(listing.get("id", "unknown"))
    directory = str(listing.get("directory", "")).strip() or listing_id
    return f"Listing '{listing_id}' ({directory}) matches canonical NAP for {brand}."


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
        "method": "listings-nap-heuristics",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
