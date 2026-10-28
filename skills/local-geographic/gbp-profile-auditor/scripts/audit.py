"""Audit Google Business Profile completeness/quality from a gbp-fixture."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

DESCRIPTION_MIN_LEN = 50
PHOTO_MIN_COUNT = 3
IDENTITY_FIELDS = ("name", "streetAddress", "addressLocality", "telephone")


def audit_gbp_profile(
    profile: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Score GBP fixture fields; return findings + Evidence.

    Hermetic: operates only on the provided gbp-fixture map (no network I/O).
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings: list[dict[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    name = _optional_string(profile.get("name"))
    street = _optional_string(profile.get("streetAddress"))
    locality = _optional_string(profile.get("addressLocality"))
    telephone = _optional_string(profile.get("telephone"))
    website = _optional_string(profile.get("website"))
    category = _optional_string(profile.get("primaryCategory"))
    description = _optional_string(profile.get("description"))
    hours_count = _hours_entry_count(profile.get("hours"))
    photo_count = _optional_int(profile.get("photoCount"))

    if name:
        findings.append(
            _finding("gbp.name", "pass", "GBP business name is present.")
        )
        evidence_items.append(
            _evidence(
                f"GBP business name is '{name}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding("gbp.name", "fail", "GBP business name is missing.")
        )
        evidence_items.append(
            _evidence(
                "GBP business name is missing from the profile fixture.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if street and locality:
        findings.append(
            _finding(
                "gbp.address",
                "pass",
                "GBP address includes streetAddress and addressLocality.",
            )
        )
        evidence_items.append(
            _evidence(
                f"GBP address includes streetAddress '{street}' and "
                f"addressLocality '{locality}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "gbp.address",
                "fail",
                "GBP address is missing streetAddress and/or addressLocality.",
            )
        )
        evidence_items.append(
            _evidence(
                "GBP address is missing streetAddress and/or addressLocality.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if telephone:
        findings.append(
            _finding("gbp.telephone", "pass", "GBP telephone is present.")
        )
        evidence_items.append(
            _evidence(
                f"GBP telephone is '{telephone}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding("gbp.telephone", "fail", "GBP telephone is missing.")
        )
        evidence_items.append(
            _evidence(
                "GBP telephone is missing from the profile fixture.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if website:
        findings.append(
            _finding("gbp.website", "pass", "GBP website URL is present.")
        )
        evidence_items.append(
            _evidence(
                f"GBP website is '{website}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding("gbp.website", "fail", "GBP website URL is missing.")
        )
        evidence_items.append(
            _evidence(
                "GBP website URL is missing from the profile fixture.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if category:
        findings.append(
            _finding("gbp.category", "pass", "GBP primary category is present.")
        )
        evidence_items.append(
            _evidence(
                f"GBP primary category is '{category}'.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding("gbp.category", "fail", "GBP primary category is missing.")
        )
        evidence_items.append(
            _evidence(
                "GBP primary category is missing from the profile fixture.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if hours_count > 0:
        findings.append(
            _finding("gbp.hours", "pass", "GBP regular hours are present.")
        )
        evidence_items.append(
            _evidence(
                f"GBP regular hours include {hours_count} day entries.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding("gbp.hours", "fail", "GBP regular hours are missing.")
        )
        evidence_items.append(
            _evidence(
                "GBP regular hours are missing from the profile fixture.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    description_len = len(description) if description else 0
    if description_len >= DESCRIPTION_MIN_LEN:
        findings.append(
            _finding(
                "gbp.description",
                "pass",
                f"GBP description meets the minimum length "
                f"(≥{DESCRIPTION_MIN_LEN} characters).",
            )
        )
    else:
        findings.append(
            _finding(
                "gbp.description",
                "fail",
                f"GBP description is below the minimum length "
                f"(≥{DESCRIPTION_MIN_LEN} characters).",
            )
        )
    evidence_items.append(
        _evidence(
            f"GBP description length is {description_len} characters "
            f"(minimum ≥{DESCRIPTION_MIN_LEN}).",
            source=source,
            observed_at=observed,
            confidence="high",
        )
    )

    if photo_count is not None and photo_count >= PHOTO_MIN_COUNT:
        findings.append(
            _finding(
                "gbp.photos",
                "pass",
                f"GBP photo count meets the minimum (≥{PHOTO_MIN_COUNT}).",
            )
        )
        evidence_items.append(
            _evidence(
                f"GBP photo count is {photo_count} (minimum ≥{PHOTO_MIN_COUNT}).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    elif photo_count is not None:
        findings.append(
            _finding(
                "gbp.photos",
                "fail",
                f"GBP photo count is below the minimum (≥{PHOTO_MIN_COUNT}).",
            )
        )
        evidence_items.append(
            _evidence(
                f"GBP photo count is {photo_count} (minimum ≥{PHOTO_MIN_COUNT}).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
    else:
        findings.append(
            _finding(
                "gbp.photos",
                "fail",
                f"GBP photo count is below the minimum (≥{PHOTO_MIN_COUNT}).",
            )
        )
        evidence_items.append(
            _evidence(
                "GBP photo count is missing from the profile fixture "
                f"(minimum ≥{PHOTO_MIN_COUNT}).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    alternate = profile.get("alternate")
    if isinstance(alternate, Mapping):
        disagreements = _identity_disagreements(profile, alternate)
        if disagreements:
            joined = ", ".join(disagreements)
            findings.append(
                _finding(
                    "gbp.profile_conflict",
                    "fail",
                    f"Primary and alternate GBP snapshots disagree on {joined}.",
                )
            )
            evidence_items.append(
                _evidence(
                    f"Primary and alternate GBP snapshots disagree on {joined}.",
                    source=source,
                    observed_at=observed,
                    confidence="needs_human_verification",
                    verification_reason=(
                        "Two GBP profile snapshots disagree on one or more "
                        "identity fields for the same business"
                    ),
                )
            )

    return {"findings": findings, "evidence": evidence_items}


def _optional_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _hours_entry_count(hours: Any) -> int:
    if not isinstance(hours, Mapping):
        return 0
    count = 0
    for value in hours.values():
        if isinstance(value, str) and value.strip():
            count += 1
    return count


def _identity_disagreements(
    primary: Mapping[str, Any],
    alternate: Mapping[str, Any],
) -> list[str]:
    disagreements: list[str] = []
    for field in IDENTITY_FIELDS:
        left = _optional_string(primary.get(field))
        right = _optional_string(alternate.get(field))
        if left is None or right is None:
            continue
        if field == "telephone":
            if _normalize_phone(left) != _normalize_phone(right):
                disagreements.append(field)
        elif _normalize_text(left) != _normalize_text(right):
            disagreements.append(field)
    return disagreements


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return digits


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
        "method": "gbp-fixture-heuristics",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
