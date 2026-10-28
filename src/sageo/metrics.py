"""Run metrics helper: cost estimates + Evidence completeness.

Writes ``metrics.json`` under a Run directory. Never invents SEO ranking
or traffic KPIs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def write_run_metrics(
    run_dir: Path,
    *,
    cost_models: Sequence[str] = (),
    usage: Mapping[str, int] | None = None,
    invocation_count: int | None = None,
) -> dict[str, Any]:
    """Compute metrics for a Run directory and write ``metrics.json``.

    Reads ``evidence.jsonl``, ``decision_log.jsonl``, and optional
    ``invocations.json`` when present. Cost estimates come from declared
    ``cost_models`` (kwargs and/or Run invocation records) plus optional
    usage stubs — never from fabricated ranking or traffic numbers.
    """
    evidence_rows = _load_jsonl(run_dir / "evidence.jsonl")
    decisions = _load_jsonl(run_dir / "decision_log.jsonl")
    invocation_rows = _load_invocations(run_dir / "invocations.json")

    resolved_models = _resolve_cost_models(cost_models, invocation_rows)
    resolved_invocations = _resolve_invocation_count(
        invocation_count, invocation_rows, decisions
    )

    completeness = _evidence_completeness(evidence_rows, decisions)
    cost = _cost_section(
        cost_models=resolved_models,
        usage=usage,
        invocation_count=resolved_invocations,
    )
    report = {
        "cost": cost,
        "evidence_completeness": completeness,
    }
    (run_dir / "metrics.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _evidence_completeness(
    evidence_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {
        str(row["id"]): row
        for row in evidence_rows
        if row.get("id") is not None and str(row.get("id")).strip() != ""
    }

    missing_evidence_ids: list[dict[str, str]] = []
    pass_count = 0
    for decision in decisions:
        decision_id = str(decision.get("decision_id") or "")
        for evidence_id in decision.get("evidence_ids") or []:
            eid = str(evidence_id)
            if eid in by_id:
                pass_count += 1
                continue
            claim = decision.get("claim") or decision.get("rationale")
            if not claim:
                claim = (
                    f"Decision {decision_id!r} references Evidence id "
                    f"{eid!r} which is absent from evidence.jsonl"
                )
            missing_evidence_ids.append(
                {
                    "pointer": f"decision_log:{decision_id}",
                    "evidence_id": eid,
                    "claim": str(claim),
                }
            )

    nhv_missing: list[dict[str, str]] = []
    for index, row in enumerate(evidence_rows):
        if row.get("confidence") != "needs_human_verification":
            continue
        reason = row.get("verification_reason")
        if reason is None or (isinstance(reason, str) and reason.strip() == ""):
            pointer = (
                f"evidence.jsonl:id={row['id']}"
                if row.get("id") is not None
                else f"evidence.jsonl:line={index + 1}"
            )
            nhv_missing.append(
                {
                    "pointer": pointer,
                    "claim": str(row.get("claim") or ""),
                }
            )
        else:
            pass_count += 1

    fail_count = len(missing_evidence_ids) + len(nhv_missing)
    return {
        "status": "pass" if fail_count == 0 else "fail",
        "pass_count": pass_count,
        "fail_count": fail_count,
        "missing_evidence_ids": missing_evidence_ids,
        "nhv_missing_verification_reason": nhv_missing,
    }


def _cost_section(
    *,
    cost_models: Sequence[str],
    usage: Mapping[str, int] | None,
    invocation_count: int | None,
) -> dict[str, Any]:
    models = [str(m) for m in cost_models]
    needs_tokens = any(
        m in ("tokens_only", "tokens_and_connector_calls", "manual_estimate")
        for m in models
    ) or not models
    needs_connectors = any(m == "tokens_and_connector_calls" for m in models)
    connectors_na = bool(models) and all(m == "tokens_only" for m in models)

    uncertainty: list[str] = []
    tokens_estimate: int | None = None
    connector_calls_estimate: int | None = None

    if usage is not None and "tokens" in usage:
        tokens_class = "from_usage_stub"
        tokens_estimate = int(usage["tokens"])
    elif needs_tokens:
        tokens_class = "estimated_from_declarations"
        uncertainty.append(
            "Token cost reported as a class estimate from cost_model "
            "declarations without recorded token usage; not a billable count."
        )
        if invocation_count is not None:
            uncertainty.append(
                f"Observed {invocation_count} invocation(s); token volume "
                "was not recorded."
            )
    else:
        tokens_class = "unknown"
        uncertainty.append("No cost_model or usage provided for tokens.")

    if connectors_na:
        connector_calls_class = "not_applicable"
    elif usage is not None and "connector_calls" in usage:
        connector_calls_class = "from_usage_stub"
        connector_calls_estimate = int(usage["connector_calls"])
    elif needs_connectors:
        connector_calls_class = "estimated_from_declarations"
        uncertainty.append(
            "Connector-call cost reported as a class estimate from "
            "cost_model declarations without recorded call usage; not a "
            "billable count."
        )
        if invocation_count is not None:
            uncertainty.append(
                f"Observed {invocation_count} invocation(s); connector-call "
                "volume was not recorded."
            )
    else:
        connector_calls_class = "unknown"
        if models:
            uncertainty.append(
                "No connector-call usage recorded for declared cost_models."
            )

    if "manual_estimate" in models:
        uncertainty.append(
            "manual_estimate cost_model present; figures are labelled "
            "estimates only."
        )

    return {
        "cost_models": models,
        "tokens_class": tokens_class,
        "connector_calls_class": connector_calls_class,
        "tokens_estimate": tokens_estimate,
        "connector_calls_estimate": connector_calls_estimate,
        "invocation_count": invocation_count,
        "uncertainty_notes": uncertainty,
    }


def _resolve_cost_models(
    cost_models: Sequence[str],
    invocation_rows: list[dict[str, Any]],
) -> list[str]:
    if cost_models:
        return [str(m) for m in cost_models]
    models: list[str] = []
    for row in invocation_rows:
        model = row.get("cost_model")
        if model is not None and str(model) not in models:
            models.append(str(model))
    return models


def _resolve_invocation_count(
    invocation_count: int | None,
    invocation_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> int | None:
    if invocation_count is not None:
        return int(invocation_count)
    if invocation_rows:
        return len(invocation_rows)
    skill_hits = 0
    for decision in decisions:
        skills = decision.get("skills") or []
        if isinstance(skills, list):
            skill_hits += len(skills)
    return skill_hits if skill_hits else None


def _load_invocations(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]
    return []


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
