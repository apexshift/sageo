"""GA4 MCP tool black box: ``call_tool`` against recorded HTTP (hermetic).

Stable tool names are SageO-owned. Skills never embed Google SDKs. Auth uses
P1 ``GA4_*`` env keys with scope ``analytics.readonly``. Property path is
``properties/{GA4_PROPERTY_ID}``. Realtime, Admin writes, and Measurement
Protocol are not exported.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from sageo.connectors.credentials import require_credentials
from sageo.connectors.nhv import nhv_evidence
from sageo.testing.recorded_http import RecordedExchange

PACK = "ga4"
REQUIRED_ENV = ("GA4_PROPERTY_ID", "GA4_CREDENTIALS_JSON")
SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

TOOL_NAMES: frozenset[str] = frozenset(
    {
        "ga4_run_report",
        "ga4_get_metadata",
    }
)


@dataclass(frozen=True)
class ToolResult:
    """MCP tool outcome: payload data or NHV Evidence (never invent metrics)."""

    ok: bool
    data: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] | None = None


def property_path(property_id: str) -> str:
    """Return Analytics Data API property resource name."""
    return f"properties/{property_id.strip()}"


def call_tool(
    name: str,
    arguments: Mapping[str, Any],
    *,
    env: Mapping[str, str | None],
    recorded: Mapping[str, RecordedExchange] | None,
    observed_at: str,
) -> ToolResult:
    """Invoke a locked GA4 tool via recorded HTTP fixtures.

    ``recorded`` maps tool name → ``RecordedExchange``. Omitting ``recorded``
    refuses to open a live Google socket (default CI path).
    """
    if name not in TOOL_NAMES:
        raise ValueError(f"unknown tool {name!r}; expected one of {sorted(TOOL_NAMES)}")
    if recorded is None:
        raise ValueError(
            "recorded HTTP fixtures are required; live Google calls are not "
            "used in default pytest/CI"
        )

    creds = require_credentials(
        env,
        REQUIRED_ENV,
        pack=PACK,
        tool=name,
        claim="GA4 Connector cannot start without credentials",
        observed_at=observed_at,
    )
    if not creds.ok:
        return ToolResult(ok=False, data=None, evidence=creds.evidence)

    exchange = recorded.get(name)
    if exchange is None:
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="upstream_error",
                claim=f"No recorded HTTP exchange for tool {name!r}",
                observed_at=observed_at,
            ),
        )

    missing_args = _missing_arguments(name, arguments)
    if missing_args:
        raise ValueError(
            f"GA4 tool {name} missing required arguments: {', '.join(missing_args)}"
        )

    prop = property_path(env.get("GA4_PROPERTY_ID") or "")
    if not _exchange_uses_property(exchange, prop):
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="upstream_error",
                claim=(
                    f"GA4 recorded exchange for {name} does not use "
                    f"property {prop!r}"
                ),
                observed_at=observed_at,
            ),
        )

    status = int(exchange.response.get("status", 0))
    body = exchange.response.get("body")

    reason = _status_to_reason(status)
    if reason is not None:
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason=reason,
                claim=f"GA4 tool {name} failed with HTTP {status}",
                observed_at=observed_at,
            ),
        )

    if not isinstance(body, Mapping):
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="upstream_error",
                claim=f"GA4 tool {name} returned a non-object body",
                observed_at=observed_at,
            ),
        )

    if _is_empty_payload(name, body):
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="empty_result",
                claim=f"GA4 tool {name} returned an empty result",
                observed_at=observed_at,
            ),
        )

    return ToolResult(ok=True, data=dict(body), evidence=None)


def _missing_arguments(name: str, arguments: Mapping[str, Any]) -> list[str]:
    required: dict[str, tuple[str, ...]] = {
        "ga4_run_report": ("dateRanges", "metrics"),
        "ga4_get_metadata": (),
    }
    return [key for key in required[name] if not arguments.get(key)]


def _exchange_uses_property(exchange: RecordedExchange, prop: str) -> bool:
    """Confirm the recorded request targets ``properties/{id}`` as a path segment."""
    url = str(exchange.request.get("url") or "")
    # Match properties/{id} before :method, /metadata, or end — avoid prefix false hits.
    markers = (f"{prop}:", f"{prop}/", f"{prop}?")
    return any(marker in url for marker in markers) or url.rstrip("/").endswith(prop)


def _status_to_reason(status: int) -> str | None:
    if status in (401, 403):
        return "auth_failed"
    if status == 429:
        return "rate_limited"
    if status in (408, 504):
        return "timeout"
    if status >= 500 or status == 0:
        return "upstream_error"
    if status >= 400:
        return "upstream_error"
    return None


def _is_empty_payload(name: str, body: Mapping[str, Any]) -> bool:
    if name == "ga4_run_report":
        rows = body.get("rows")
        return isinstance(rows, list) and len(rows) == 0
    if name == "ga4_get_metadata":
        dimensions = body.get("dimensions")
        metrics = body.get("metrics")
        empty_dims = isinstance(dimensions, list) and len(dimensions) == 0
        empty_metrics = isinstance(metrics, list) and len(metrics) == 0
        return empty_dims and empty_metrics
    return False
