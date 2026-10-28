"""GSC MCP tool black box: ``call_tool`` against recorded HTTP (hermetic).

Stable tool names are SageO-owned. Skills never embed Google SDKs. Auth uses
P1 ``GSC_*`` env keys with scope ``webmasters.readonly``. Write tools are not
exported.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote

from sageo.connectors.credentials import require_credentials
from sageo.connectors.nhv import nhv_evidence
from sageo.testing.recorded_http import RecordedExchange

PACK = "gsc"
REQUIRED_ENV = ("GSC_CLIENT_EMAIL", "GSC_PRIVATE_KEY", "GSC_PROPERTY_URL")
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

TOOL_NAMES: frozenset[str] = frozenset(
    {
        "gsc_search_analytics_query",
        "gsc_url_inspect",
        "gsc_sitemaps_list",
    }
)


@dataclass(frozen=True)
class ToolResult:
    """MCP tool outcome: payload data or NHV Evidence (never both invent metrics)."""

    ok: bool
    data: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] | None = None


def call_tool(
    name: str,
    arguments: Mapping[str, Any],
    *,
    env: Mapping[str, str | None],
    recorded: Mapping[str, RecordedExchange] | None,
    observed_at: str,
) -> ToolResult:
    """Invoke a locked GSC tool via recorded HTTP fixtures.

    ``recorded`` maps tool name → ``RecordedExchange``. Default CI must pass
    fixtures; omitting ``recorded`` refuses to open a live Google socket.
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
        claim="GSC Connector cannot start without credentials",
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
            f"GSC tool {name} missing required arguments: {', '.join(missing_args)}"
        )

    site_url = (env.get("GSC_PROPERTY_URL") or "").strip()
    if not _exchange_uses_property(exchange, site_url):
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="upstream_error",
                claim=(
                    f"GSC recorded exchange for {name} does not use "
                    f"GSC_PROPERTY_URL={site_url!r}"
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
                claim=f"GSC tool {name} failed with HTTP {status}",
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
                claim=f"GSC tool {name} returned a non-object body",
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
                claim=f"GSC tool {name} returned an empty result",
                observed_at=observed_at,
            ),
        )

    return ToolResult(ok=True, data=dict(body), evidence=None)


def _missing_arguments(name: str, arguments: Mapping[str, Any]) -> list[str]:
    required: dict[str, tuple[str, ...]] = {
        "gsc_search_analytics_query": ("startDate", "endDate"),
        "gsc_url_inspect": ("inspectionUrl",),
        "gsc_sitemaps_list": (),
    }
    return [key for key in required[name] if not arguments.get(key)]


def _exchange_uses_property(exchange: RecordedExchange, site_url: str) -> bool:
    """Confirm the recorded request targets the env property (siteUrl)."""
    encoded = quote(site_url, safe="")
    url = str(exchange.request.get("url") or "")
    if site_url in url or encoded in url:
        return True
    body = exchange.request.get("body")
    if isinstance(body, Mapping) and body.get("siteUrl") == site_url:
        return True
    return False


def _status_to_reason(status: int) -> str | None:
    if status in (401, 403):
        return "auth_failed"
    if status == 429:
        return "rate_limited"
    if status == 408 or status == 504:
        return "timeout"
    if status >= 500 or status == 0:
        return "upstream_error"
    if status >= 400:
        return "upstream_error"
    return None


def _is_empty_payload(name: str, body: Mapping[str, Any]) -> bool:
    if name == "gsc_search_analytics_query":
        rows = body.get("rows")
        return isinstance(rows, list) and len(rows) == 0
    if name == "gsc_sitemaps_list":
        sitemaps = body.get("sitemap")
        return isinstance(sitemaps, list) and len(sitemaps) == 0
    if name == "gsc_url_inspect":
        return not body.get("inspectionResult")
    return False
