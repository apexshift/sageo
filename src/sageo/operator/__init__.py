"""Operator runtime bridge: desktop façade over Orchestrator run seams.

Validate a local SageO checkout + interpreter, and start thin_audit Runs from
the locked New Run field model. No Electron UI lives here.
"""

from sageo.operator.bridge import (
    ReadyCheckResult,
    start_thin_audit_run,
    validate_runtime,
)

__all__ = [
    "ReadyCheckResult",
    "start_thin_audit_run",
    "validate_runtime",
]
