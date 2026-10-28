"""NHV Evidence mapping for Connector failures.

Locked ``verification_reason`` set from the P3 Spec. ``source`` is
``{pack}/{tool}`` so Skills can cite which Connector tool failed.
"""

from __future__ import annotations

from typing import Any

VERIFICATION_REASONS: frozenset[str] = frozenset(
    {
        "missing_credentials",
        "auth_failed",
        "rate_limited",
        "timeout",
        "upstream_error",
        "empty_result",
    }
)


def nhv_evidence(
    *,
    pack: str,
    tool: str,
    verification_reason: str,
    claim: str,
    observed_at: str,
) -> dict[str, Any]:
    """Build NHV Evidence for a Connector failure.

    Returns an Evidence record with ``confidence: needs_human_verification``
    and a locked ``verification_reason``. Does not invent metrics.
    """
    if verification_reason not in VERIFICATION_REASONS:
        raise ValueError(
            f"verification_reason must be one of {sorted(VERIFICATION_REASONS)}; "
            f"got {verification_reason!r}"
        )
    return {
        "claim": claim,
        "source": f"{pack}/{tool}",
        "observed_at": observed_at,
        "confidence": "needs_human_verification",
        "verification_reason": verification_reason,
    }
