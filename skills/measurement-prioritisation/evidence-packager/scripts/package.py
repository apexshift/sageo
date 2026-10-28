"""Package an evidence-bundle into a review-ready package (partial Evidence)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

REQUIRED_EVIDENCE_FIELDS = ("claim", "source", "observed_at", "confidence")
VALID_CONFIDENCE = frozenset(
    {"high", "medium", "low", "needs_human_verification"}
)


def package_evidence(
    evidence_bundle: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Assemble a review-ready package from upstream findings + Evidence.

    Hermetic: operates only on the provided evidence-bundle map (no network I/O).
    ``evidence_requirement: partial`` — only packaging claims emit Evidence.
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not isinstance(evidence_bundle, Mapping):
        raise TypeError("evidence_bundle must be a mapping")

    findings_in = evidence_bundle.get("findings", [])
    evidence_in = evidence_bundle.get("evidence", [])
    if not isinstance(findings_in, list):
        raise TypeError("evidence_bundle findings must be a list")
    if not isinstance(evidence_in, list):
        raise TypeError("evidence_bundle evidence must be a list")

    ranked_ids = _parse_ranked_ids(evidence_bundle.get("ranked_ids"))

    packaged_findings = [_normalize_finding(item) for item in findings_in]
    packaged_evidence = [_normalize_evidence_record(item) for item in evidence_in]

    incomplete = _incomplete_evidence_indexes(packaged_evidence)
    nhv_count = sum(
        1
        for item in packaged_evidence
        if item.get("confidence") == "needs_human_verification"
    )
    finding_count = len(packaged_findings)
    evidence_count = len(packaged_evidence)

    ready = finding_count + evidence_count > 0 and not incomplete
    package = {
        "ready_for_review": ready,
        "finding_count": finding_count,
        "evidence_count": evidence_count,
        "nhv_count": nhv_count,
        "ranked_ids": ranked_ids,
        "findings": packaged_findings,
        "evidence": packaged_evidence,
    }

    out_findings: list[dict[str, str]] = []
    out_evidence: list[dict[str, str]] = []

    out_evidence.append(
        _evidence(
            f"Bundled {finding_count} findings and {evidence_count} Evidence "
            f"records ({nhv_count} needs_human_verification).",
            source=source,
            observed_at=observed,
            confidence="high",
        )
    )

    if finding_count == 0 and evidence_count == 0:
        out_findings.append(
            _finding(
                "package.ready",
                "fail",
                "Evidence bundle is empty and not review-ready.",
            )
        )
        return {
            "package": package,
            "findings": out_findings,
            "evidence": out_evidence,
        }

    if incomplete:
        out_findings.append(
            _finding(
                "package.ready",
                "fail",
                "Evidence bundle is not review-ready due to incomplete Evidence.",
            )
        )
        out_findings.append(
            _finding(
                "package.incomplete",
                "fail",
                f"{len(incomplete)} Evidence record(s) are missing required fields.",
            )
        )
        for index, missing in incomplete:
            out_evidence.append(
                _evidence(
                    f"Evidence record {index} is missing required field(s): "
                    f"{', '.join(missing)}.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
        return {
            "package": package,
            "findings": out_findings,
            "evidence": out_evidence,
        }

    out_findings.append(
        _finding(
            "package.ready",
            "pass",
            "Evidence bundle is review-ready "
            f"({finding_count} findings, {evidence_count} Evidence records).",
        )
    )
    if ranked_ids:
        out_evidence.append(
            _evidence(
                "Preserved ranked_ids order: " + ", ".join(ranked_ids) + ".",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    if nhv_count > 0:
        out_findings.append(
            _finding(
                "package.nhv_pending",
                "fail",
                "Package includes "
                f"{nhv_count} Evidence record(s) marked needs_human_verification.",
            )
        )
        out_evidence.append(
            _evidence(
                f"{nhv_count} Evidence record(s) require human verification "
                "before acting on dependent claims.",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    return {
        "package": package,
        "findings": out_findings,
        "evidence": out_evidence,
    }


def _parse_ranked_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError("evidence_bundle ranked_ids must be a list")
    ranked: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise TypeError("evidence_bundle ranked_ids must be non-empty strings")
        ranked.append(item.strip())
    return ranked


def _normalize_finding(item: Any) -> dict[str, str]:
    if not isinstance(item, Mapping):
        raise TypeError("evidence_bundle findings must be mappings")
    return {
        "id": str(item.get("id", "unknown")),
        "status": str(item.get("status", "fail")),
        "summary": str(item.get("summary", "")),
    }


def _normalize_evidence_record(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise TypeError("evidence_bundle evidence must be mappings")
    return dict(item)


def _incomplete_evidence_indexes(
    evidence_items: Sequence[Mapping[str, Any]],
) -> list[tuple[int, list[str]]]:
    incomplete: list[tuple[int, list[str]]] = []
    for offset, item in enumerate(evidence_items, start=1):
        missing: list[str] = []
        for field in REQUIRED_EVIDENCE_FIELDS:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                missing.append(field)
                continue
            if field == "confidence" and value not in VALID_CONFIDENCE:
                missing.append(field)
        confidence = item.get("confidence")
        if (
            confidence == "needs_human_verification"
            and "confidence" not in missing
            and (
                not isinstance(item.get("verification_reason"), str)
                or not str(item.get("verification_reason")).strip()
            )
        ):
            missing.append("verification_reason")
        if missing:
            incomplete.append((offset, missing))
    return incomplete


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
        "method": "evidence-bundle-package",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
