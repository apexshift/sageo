"""Operator runtime bridge: desktop façade over Orchestrator run seams.

Validate a local SageO checkout + interpreter, persist runtime config, start
thin_audit Runs, list Runs, read Progress snapshots, watch active Runs, and
resume Human review gates. Electron UI lives under ``apps/operator-desktop/``.
"""

from sageo.operator.bridge import (
    AgentProgress,
    FindingRow,
    ProgressSnapshot,
    ReadyCheckResult,
    ReviewSnapshot,
    RunSummary,
    StartThinAuditResult,
    connector_credential_warnings,
    get_progress,
    get_review,
    list_findings,
    list_runs,
    load_thin_audit_agents,
    resume_run,
    resume_run_from_checkout,
    start_thin_audit_from_checkout,
    start_thin_audit_run,
    validate_runtime,
    watch_run_progress,
)
from sageo.operator.session import (
    LaunchDecision,
    RuntimeConfig,
    finish_wizard,
    load_runtime_config,
    resolve_launch,
    save_runtime_config,
)

__all__ = [
    "AgentProgress",
    "FindingRow",
    "LaunchDecision",
    "ProgressSnapshot",
    "ReadyCheckResult",
    "ReviewSnapshot",
    "RunSummary",
    "RuntimeConfig",
    "StartThinAuditResult",
    "connector_credential_warnings",
    "finish_wizard",
    "get_progress",
    "get_review",
    "list_findings",
    "list_runs",
    "load_runtime_config",
    "load_thin_audit_agents",
    "resolve_launch",
    "resume_run",
    "resume_run_from_checkout",
    "save_runtime_config",
    "start_thin_audit_from_checkout",
    "start_thin_audit_run",
    "validate_runtime",
    "watch_run_progress",
]
