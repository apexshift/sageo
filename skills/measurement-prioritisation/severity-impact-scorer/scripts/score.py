"""Score issue-list items by severity × impact and emit Evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

SCORE_MIN = 1
SCORE_MAX = 5


def score_severity_impact(
    issue_list: Mapping[str, Any],
    *,
    source: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Score issues by severity × impact; return findings + Evidence.

    Hermetic: operates only on the provided issue-list map (no network I/O).
    """
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not isinstance(issue_list, Mapping):
        raise TypeError("issue_list must be a mapping")

    raw_issues = issue_list.get("issues", [])
    if not isinstance(raw_issues, list):
        raise TypeError("issue_list issues must be a list")

    if len(raw_issues) == 0:
        return {
            "findings": [
                _finding(
                    "priority.scored",
                    "fail",
                    "No issues available to score by severity × impact.",
                )
            ],
            "evidence": [
                _evidence(
                    "Issue list contains 0 issues to score.",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            ],
        }

    scored: list[tuple[str, int, int, int]] = []
    incompletes: list[tuple[str, str]] = []
    evidence_items: list[dict[str, str]] = []

    for issue in raw_issues:
        if not isinstance(issue, Mapping):
            raise TypeError("issue_list issues must be mappings")
        issue_id = _issue_id(issue)
        severity, severity_ok = _parse_score(issue.get("severity"))
        impact, impact_ok = _parse_score(issue.get("impact"))

        if severity_ok and impact_ok:
            assert severity is not None and impact is not None
            product = severity * impact
            scored.append((issue_id, severity, impact, product))
            evidence_items.append(
                _evidence(
                    f"Issue '{issue_id}' score is {product} "
                    f"(severity {severity} × impact {impact}).",
                    source=source,
                    observed_at=observed,
                    confidence="high",
                )
            )
            continue

        if not severity_ok and not impact_ok:
            field = "severity and impact"
        elif not severity_ok:
            field = "severity"
        else:
            field = "impact"
        incompletes.append((issue_id, field))
        evidence_items.append(
            _evidence(
                f"Issue '{issue_id}' is missing a valid {field} "
                f"(require integers {SCORE_MIN}–{SCORE_MAX}).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )

    findings: list[dict[str, str]] = []

    if incompletes:
        findings.append(
            _finding(
                "priority.scored",
                "fail",
                "Severity × impact scoring failed for one or more issues.",
            )
        )
        findings.append(
            _finding(
                "priority.incomplete",
                "fail",
                f"{len(incompletes)} issue(s) are missing or have invalid "
                f"severity/impact (require integers {SCORE_MIN}–{SCORE_MAX}).",
            )
        )
    else:
        ranked = sorted(scored, key=lambda row: (-row[3], row[0]))
        findings.append(
            _finding(
                "priority.scored",
                "pass",
                f"Scored {len(ranked)} issues by severity × impact.",
            )
        )
        top_id, _, _, top_score = ranked[0]
        findings.append(
            _finding(
                "priority.rank",
                "pass",
                f"Top priority is '{top_id}' with score {top_score}.",
            )
        )
        evidence_items.append(
            _evidence(
                f"Ranked {len(ranked)} issues; top priority is '{top_id}' "
                f"(score {top_score}).",
                source=source,
                observed_at=observed,
                confidence="high",
            )
        )
        # Reorder per-issue Evidence to match rank (product desc, id asc).
        per_issue = evidence_items[:-1]
        by_id = {
            row[0]: item
            for row, item in zip(scored, per_issue, strict=True)
        }
        evidence_items = [by_id[row[0]] for row in ranked] + [evidence_items[-1]]

    alternate = issue_list.get("alternate_issues")
    if isinstance(alternate, list) and scored and not incompletes:
        primary_scores = {issue_id: product for issue_id, _, _, product in scored}
        conflicts: list[tuple[str, int, int]] = []
        for alt in alternate:
            if not isinstance(alt, Mapping):
                continue
            alt_id = _issue_id(alt)
            if alt_id not in primary_scores:
                continue
            alt_severity, sev_ok = _parse_score(alt.get("severity"))
            alt_impact, imp_ok = _parse_score(alt.get("impact"))
            if not (sev_ok and imp_ok):
                continue
            assert alt_severity is not None and alt_impact is not None
            alt_score = alt_severity * alt_impact
            primary_score = primary_scores[alt_id]
            if alt_score != primary_score:
                conflicts.append((alt_id, primary_score, alt_score))

        if conflicts:
            findings.append(
                _finding(
                    "priority.score_conflict",
                    "fail",
                    "Primary and alternate issue lists disagree on score for "
                    f"{len(conflicts)} issue(s).",
                )
            )
            for issue_id, primary_score, alt_score in conflicts:
                evidence_items.append(
                    _evidence(
                        f"Primary and alternate scores disagree for issue "
                        f"'{issue_id}' ({primary_score} vs {alt_score}).",
                        source=source,
                        observed_at=observed,
                        confidence="needs_human_verification",
                        verification_reason=(
                            "Two issue-list snapshots disagree on severity × "
                            "impact score for the same issue id"
                        ),
                    )
                )

    return {"findings": findings, "evidence": evidence_items}


def _issue_id(issue: Mapping[str, Any]) -> str:
    raw = issue.get("id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "unknown"


def _parse_score(value: Any) -> tuple[int | None, bool]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None, False
    if value < SCORE_MIN or value > SCORE_MAX:
        return None, False
    return value, True


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
        "method": "severity-impact-product",
    }
    if verification_reason is not None:
        item["verification_reason"] = verification_reason
    return item
