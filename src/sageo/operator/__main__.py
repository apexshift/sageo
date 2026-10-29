"""CLI for Electron main: JSON ready-check, launch, Start, Progress."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sageo.operator.bridge import (
    FindingRow,
    ProgressSnapshot,
    ReadyCheckResult,
    ReviewSnapshot,
    RunSummary,
    StartThinAuditResult,
    get_progress,
    get_review,
    list_findings,
    list_runs,
    resume_run_from_checkout,
    start_thin_audit_from_checkout,
    validate_runtime,
    watch_run_progress,
)
from sageo.operator.session import (
    RuntimeConfig,
    finish_wizard,
    resolve_launch,
)


def _ready_dict(ready: ReadyCheckResult | None) -> dict[str, Any] | None:
    if ready is None:
        return None
    return {
        "ok": ready.ok,
        "errors": list(ready.errors),
        "checkout_root": str(ready.checkout_root),
        "interpreter": str(ready.interpreter),
        "runs_root": str(ready.runs_root),
    }


def _decision_dict(decision: Any) -> dict[str, Any]:
    config = decision.config
    return {
        "view": decision.view,
        "errors": list(decision.errors),
        "config": None
        if config is None
        else {
            "checkout_root": config.checkout_root,
            "interpreter": config.interpreter,
            "runs_root": config.runs_root,
        },
        "ready": _ready_dict(decision.ready),
    }


def _summary_dict(row: RunSummary) -> dict[str, Any]:
    return {
        "run_id": row.run_id,
        "goal": row.goal,
        "site_host": row.site_host,
        "reach": row.reach,
        "status": row.status,
    }


def _progress_dict(snap: ProgressSnapshot) -> dict[str, Any]:
    return {
        "run_id": snap.run_id,
        "gate_state": snap.gate_state,
        "paused_agent": snap.paused_agent,
        "empty_schedule": snap.empty_schedule,
        "agents": [{"name": a.name, "status": a.status} for a in snap.agents],
    }


def _start_dict(result: StartThinAuditResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "run_dir": str(result.run_dir),
        "gate_state": result.gate_state,
        "warnings": list(result.warnings),
        "progress": _progress_dict(get_progress(result.run_dir.parent, result.run_id)),
    }


def _finding_dict(row: FindingRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title,
        "agent": row.agent,
        "confidence": row.confidence,
        "claim": row.claim,
        "source": row.source,
        "method": row.method,
        "observed_at": row.observed_at,
        "verification_reason": row.verification_reason,
        "is_nhv": row.is_nhv,
    }


def _review_dict(review: ReviewSnapshot) -> dict[str, Any]:
    return {
        "run_id": review.run_id,
        "gate_state": review.gate_state,
        "paused_agent": review.paused_agent,
        "gate_open": review.gate_open,
        "empty_message": review.empty_message,
        "decision": review.decision,
        "evidence_ids": list(review.evidence_ids),
        "linked_findings": [_finding_dict(row) for row in review.linked_findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sageo.operator")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate", help="Run bridge validate_runtime")
    validate_p.add_argument("--checkout-root", required=True)
    validate_p.add_argument("--interpreter", required=True)
    validate_p.add_argument("--runs-root", default=None)

    resolve_p = sub.add_parser("resolve-launch", help="Wizard vs shell decision")
    resolve_p.add_argument("--config-path", required=True)

    finish_p = sub.add_parser("finish-wizard", help="Validate, persist, open shell")
    finish_p.add_argument("--config-path", required=True)
    finish_p.add_argument("--checkout-root", required=True)
    finish_p.add_argument("--interpreter", required=True)
    finish_p.add_argument("--runs-root", default=None)

    start_p = sub.add_parser("start-thin-audit", help="Start thin_audit from New Run")
    start_p.add_argument("--checkout-root", required=True)
    start_p.add_argument("--runs-root", required=True)
    start_p.add_argument("--site-url", required=True)
    start_p.add_argument("--reach", default="national")
    start_p.add_argument("--goal", default=None)
    start_p.add_argument("--gsc-property", default=None)
    start_p.add_argument("--ga4-property", default=None)
    start_p.add_argument("--run-id", default=None)
    start_p.add_argument("--observed-at", default=None)

    list_p = sub.add_parser("list-runs", help="List Runs for sidebar")
    list_p.add_argument("--runs-root", required=True)

    progress_p = sub.add_parser("get-progress", help="Progress snapshot")
    progress_p.add_argument("--runs-root", required=True)
    progress_p.add_argument("--run-id", required=True)

    watch_p = sub.add_parser(
        "watch-progress",
        help="Emit Progress JSON lines until idle",
    )
    watch_p.add_argument("--runs-root", required=True)
    watch_p.add_argument("--run-id", required=True)
    watch_p.add_argument("--poll-interval", type=float, default=1.0)

    findings_p = sub.add_parser("list-findings", help="Findings Evidence rows")
    findings_p.add_argument("--runs-root", required=True)
    findings_p.add_argument("--run-id", required=True)
    findings_p.add_argument("--confidence", default=None)
    findings_p.add_argument("--agent", default=None)

    review_p = sub.add_parser("get-review", help="Review gate snapshot")
    review_p.add_argument("--runs-root", required=True)
    review_p.add_argument("--run-id", required=True)

    resume_p = sub.add_parser("resume-run", help="Approve/reject gate via resume")
    resume_p.add_argument("--checkout-root", required=True)
    resume_p.add_argument("--runs-root", required=True)
    resume_p.add_argument("--run-id", required=True)
    resume_p.add_argument("--approved", required=True, choices=["true", "false"])
    resume_p.add_argument("--operator-note", default=None)
    resume_p.add_argument("--observed-at", default=None)

    args = parser.parse_args(argv)

    if args.command == "validate":
        ready = validate_runtime(
            checkout_root=args.checkout_root,
            interpreter=args.interpreter,
            runs_root=args.runs_root,
        )
        json.dump(_ready_dict(ready), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if ready.ok else 1

    if args.command == "resolve-launch":
        decision = resolve_launch(Path(args.config_path))
        json.dump(_decision_dict(decision), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if decision.view == "shell" else 1

    if args.command == "finish-wizard":
        decision = finish_wizard(
            Path(args.config_path),
            RuntimeConfig(
                checkout_root=args.checkout_root,
                interpreter=args.interpreter,
                runs_root=args.runs_root,
            ),
        )
        json.dump(_decision_dict(decision), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if decision.view == "shell" else 1

    if args.command == "start-thin-audit":
        observed = args.observed_at or datetime.now(timezone.utc).isoformat()
        result = start_thin_audit_from_checkout(
            checkout_root=args.checkout_root,
            runs_root=args.runs_root,
            site_url=args.site_url,
            reach=args.reach,
            goal=args.goal,
            gsc_property=args.gsc_property,
            ga4_property=args.ga4_property,
            run_id=args.run_id,
            observed_at=observed,
        )
        json.dump(_start_dict(result), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "list-runs":
        rows = [_summary_dict(row) for row in list_runs(args.runs_root)]
        json.dump(rows, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "get-progress":
        snap = get_progress(args.runs_root, args.run_id)
        json.dump(_progress_dict(snap), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "watch-progress":
        for snap in watch_run_progress(
            args.runs_root,
            args.run_id,
            poll_interval=args.poll_interval,
        ):
            json.dump(_progress_dict(snap), sys.stdout, sort_keys=True)
            sys.stdout.write("\n")
            sys.stdout.flush()
        return 0

    if args.command == "list-findings":
        rows = [
            _finding_dict(row)
            for row in list_findings(
                args.runs_root,
                args.run_id,
                confidence=args.confidence,
                agent=args.agent,
            )
        ]
        json.dump(rows, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "get-review":
        review = get_review(args.runs_root, args.run_id)
        json.dump(_review_dict(review), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if args.command == "resume-run":
        observed = args.observed_at or datetime.now(timezone.utc).isoformat()
        result = resume_run_from_checkout(
            checkout_root=args.checkout_root,
            runs_root=args.runs_root,
            run_id=args.run_id,
            approved=args.approved == "true",
            observed_at=observed,
            operator_note=args.operator_note,
        )
        payload = {
            "run_id": result.run_id,
            "gate_state": result.gate_state,
            "review": _review_dict(get_review(args.runs_root, args.run_id)),
            "progress": _progress_dict(get_progress(args.runs_root, args.run_id)),
        }
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
