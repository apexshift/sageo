"""crawl-serp MCP tool black box: ``call_tool`` against recorded HTTP (hermetic).

SageO-owned tools backed by DataForSEO On-Page + SERP. Auth: ``CRAWL_SERP_API_KEY``
as ``login:password`` for Basic auth; ``CRAWL_SERP_BASE_URL`` for the API host.
Skills never import DataForSEO SDKs. Not a wholesale vendor MCP passthrough.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Mapping

from sageo.connectors.credentials import require_credentials
from sageo.connectors.nhv import nhv_evidence
from sageo.testing.recorded_http import RecordedExchange

PACK = "crawl_serp"
REQUIRED_ENV = ("CRAWL_SERP_API_KEY", "CRAWL_SERP_BASE_URL")
DEFAULT_BASE_URL = "https://api.dataforseo.com"

TOOL_NAMES: frozenset[str] = frozenset(
    {
        "crawl_start_task",
        "crawl_site_summary",
        "crawl_page_issues",
        "serp_google_organic",
    }
)


@dataclass(frozen=True)
class ToolResult:
    """MCP tool outcome: SageO-shaped data or NHV Evidence."""

    ok: bool
    data: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] | None = None


def basic_auth_header(api_key: str) -> str:
    """Encode ``login:password`` as an HTTP Basic Authorization value."""
    token = base64.b64encode(api_key.encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def call_tool(
    name: str,
    arguments: Mapping[str, Any],
    *,
    env: Mapping[str, str | None],
    recorded: Mapping[str, RecordedExchange] | None,
    observed_at: str,
) -> ToolResult:
    """Invoke a locked crawl/SERP tool via recorded HTTP fixtures."""
    if name not in TOOL_NAMES:
        raise ValueError(f"unknown tool {name!r}; expected one of {sorted(TOOL_NAMES)}")
    if recorded is None:
        raise ValueError(
            "recorded HTTP fixtures are required; live DataForSEO calls are not "
            "used in default pytest/CI"
        )

    creds = require_credentials(
        env,
        REQUIRED_ENV,
        pack=PACK,
        tool=name,
        claim="crawl-serp Connector cannot start without credentials",
        observed_at=observed_at,
    )
    if not creds.ok:
        return ToolResult(ok=False, data=None, evidence=creds.evidence)

    api_key = (env.get("CRAWL_SERP_API_KEY") or "").strip()
    if ":" not in api_key:
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="missing_credentials",
                claim=(
                    "CRAWL_SERP_API_KEY must be login:password for DataForSEO Basic auth"
                ),
                observed_at=observed_at,
            ),
        )

    base_url = (env.get("CRAWL_SERP_BASE_URL") or "").rstrip("/")
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
            f"crawl-serp tool {name} missing required arguments: "
            f"{', '.join(missing_args)}"
        )

    if not _exchange_uses_base_url(exchange, base_url):
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="upstream_error",
                claim=(
                    f"crawl-serp recorded exchange for {name} does not use "
                    f"CRAWL_SERP_BASE_URL={base_url!r}"
                ),
                observed_at=observed_at,
            ),
        )

    expected_auth = basic_auth_header(api_key)
    headers = exchange.request.get("headers")
    recorded_auth = (
        headers.get("Authorization") if isinstance(headers, Mapping) else None
    )
    if recorded_auth != expected_auth:
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="auth_failed",
                claim=(
                    "crawl-serp recorded Authorization does not match "
                    "Basic auth from CRAWL_SERP_API_KEY"
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
                claim=f"crawl-serp tool {name} failed with HTTP {status}",
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
                claim=f"crawl-serp tool {name} returned a non-object body",
                observed_at=observed_at,
            ),
        )

    normalized = _normalize(name, body, arguments)
    if normalized is None:
        return ToolResult(
            ok=False,
            data=None,
            evidence=nhv_evidence(
                pack=PACK,
                tool=name,
                verification_reason="empty_result",
                claim=f"crawl-serp tool {name} returned an empty result",
                observed_at=observed_at,
            ),
        )

    return ToolResult(ok=True, data=normalized, evidence=None)


def _missing_arguments(name: str, arguments: Mapping[str, Any]) -> list[str]:
    required: dict[str, tuple[str, ...]] = {
        "crawl_start_task": ("target", "max_crawl_pages"),
        "crawl_site_summary": ("task_id",),
        "crawl_page_issues": ("task_id",),
        "serp_google_organic": ("keyword",),
    }
    missing = [key for key in required[name] if arguments.get(key) in (None, "")]
    if name == "serp_google_organic":
        if not arguments.get("location_code") and not arguments.get("language_code"):
            missing.append("location_code|language_code")
    return missing


def _exchange_uses_base_url(exchange: RecordedExchange, base_url: str) -> bool:
    url = str(exchange.request.get("url") or "")
    return url.startswith(base_url + "/") or url == base_url


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


def _normalize(
    name: str,
    body: Mapping[str, Any],
    arguments: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Map DataForSEO envelopes to stable SageO tool outputs."""
    tasks = body.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return None
    task0 = tasks[0]
    if not isinstance(task0, Mapping):
        return None

    if name == "crawl_start_task":
        task_id = task0.get("id")
        if not task_id:
            return None
        return {"task_id": task_id}

    if name == "crawl_site_summary":
        result = task0.get("result")
        if not isinstance(result, list) or not result:
            return None
        summary = result[0]
        if not isinstance(summary, Mapping):
            return None
        progress = summary.get("crawl_progress")
        if not progress:
            return None
        return {
            "task_id": arguments.get("task_id") or task0.get("id"),
            "crawl_progress": progress,
            "crawl_status": summary.get("crawl_status"),
            "domain_info": summary.get("domain_info"),
            "page_metrics": summary.get("page_metrics"),
        }

    if name == "crawl_page_issues":
        result = task0.get("result")
        if not isinstance(result, list) or not result:
            return None
        page_block = result[0]
        if not isinstance(page_block, Mapping):
            return None
        items = page_block.get("items")
        if not isinstance(items, list) or not items:
            return None
        return {
            "task_id": arguments.get("task_id") or task0.get("id"),
            "items": items,
        }

    if name == "serp_google_organic":
        result = task0.get("result")
        if not isinstance(result, list) or not result:
            return None
        serp = result[0]
        if not isinstance(serp, Mapping):
            return None
        items = serp.get("items")
        if not isinstance(items, list) or not items:
            return None
        return {
            "keyword": serp.get("keyword") or arguments.get("keyword"),
            "items": items,
        }

    return None
