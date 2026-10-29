"""Operator runtime bridge: desktop façade over Orchestrator run seams.

Validate a local SageO checkout + interpreter, start thin_audit Runs, list
Runs, read Progress snapshots, watch active Runs, and resume Human review
gates. No Electron UI lives here.
"""

from sageo.operator.bridge import (
    AgentProgress,
    ProgressSnapshot,
    ReadyCheckResult,
    RunSummary,
    get_progress,
    list_runs,
    resume_run,
    start_thin_audit_run,
    validate_runtime,
    watch_run_progress,
)

__all__ = [
    "AgentProgress",
    "ProgressSnapshot",
    "ReadyCheckResult",
    "RunSummary",
    "get_progress",
    "list_runs",
    "resume_run",
    "start_thin_audit_run",
    "validate_runtime",
    "watch_run_progress",
]
