"""Refuse Connector start when required env credentials are missing.

Emits NHV Evidence with ``verification_reason: missing_credentials``.
Never invents metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from sageo.connectors.nhv import nhv_evidence


@dataclass(frozen=True)
class CredentialCheck:
    """Result of a credential gate check."""

    ok: bool
    evidence: dict[str, Any] | None = None


def require_credentials(
    env: Mapping[str, str | None],
    required_keys: Sequence[str],
    *,
    pack: str,
    tool: str,
    claim: str,
    observed_at: str,
) -> CredentialCheck:
    """Return ok when every required key is present and non-empty in ``env``.

    Otherwise refuse start with NHV Evidence (``missing_credentials``).
    """
    missing = [
        key
        for key in required_keys
        if not (env.get(key) or "").strip()
    ]
    if not missing:
        return CredentialCheck(ok=True, evidence=None)
    return CredentialCheck(
        ok=False,
        evidence=nhv_evidence(
            pack=pack,
            tool=tool,
            verification_reason="missing_credentials",
            claim=claim,
            observed_at=observed_at,
        ),
    )
