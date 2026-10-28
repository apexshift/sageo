# crawl-serp Connector pack

SageO-owned read-only MCP surface for crawl issues and Google organic SERP,
backed by DataForSEO. Skills call these tool names; they do not embed vendor
SDKs or the wholesale vendor MCP.

**Runtime:** `sageo.connectors.crawl_serp.call_tool`  
**Env (P1 names):**  
- `CRAWL_SERP_API_KEY` — DataForSEO `login:password` (Basic auth)  
- `CRAWL_SERP_BASE_URL` — `https://api.dataforseo.com`

## Tools

| Tool | Role |
| --- | --- |
| `crawl_start_task` | On-Page `task_post` → `task_id` |
| `crawl_site_summary` | On-Page summary / `crawl_progress` |
| `crawl_page_issues` | On-Page pages + checks |
| `serp_google_organic` | Google organic + common SERP elements |

## Async crawl flow

1. `crawl_start_task` → `task_id`
2. Poll `crawl_site_summary` until `crawl_progress` is finished
3. `crawl_page_issues` with that `task_id`

Hermetic fixtures short-circuit to a finished summary.

## Failures → NHV

Missing env or malformed `login:password` refuses start with
`missing_credentials`. Upstream failures map to `auth_failed` | `rate_limited` |
`timeout` | `upstream_error` | `empty_result`. Evidence `source` is
`crawl_serp/<tool>`.

## Excluded

Lighthouse-as-separate surface; billed AI Summary endpoints; write/mutation of
client sites; wholesale vendor MCP passthrough.

## Tests

Hermetic recorded HTTP under `tests/connectors/crawl-serp/` — no live
DataForSEO calls in default pytest/CI.
