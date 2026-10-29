"""Operator runtime bridge: desktop façade over Orchestrator run seams.

Validate a local SageO checkout + interpreter, persist runtime config, start
thin_audit Runs, list Runs, read Progress snapshots, watch active Runs, and
resume Human review gates. Electron UI lives under ``apps/operator-desktop/``.
"""

from sageo.operator.bridge import (
    AgentProgress,
    ProgressSnapshot,
    ReadyCheckResult,
    RunSummary,
    StartThinAuditResult,
    connector_credential_warnings,
    get_progress,
    list_runs,
    load_thin_audit_agents,
    resume_run,
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
    "LaunchDecision",
    "ProgressSnapshot",
    "ReadyCheckResult",
    "RunSummary",
    "RuntimeConfig",
    "StartThinAuditResult",
    "connector_credential_warnings",
    "finish_wizard",
    "get_progress",
    "list_runs",
    "load_runtime_config",
    "load_thin_audit_agents",
    "resolve_launch",
    "resume_run",
    "save_runtime_config",
    "start_thin_audit_from_checkout",
    "start_thin_audit_run",
    "validate_runtime",
    "watch_run_progress",
]
