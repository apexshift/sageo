# GSC Connector pack

SageO-owned read-only MCP surface for Google Search Console. Skills call these
tool names; they do not embed Google SDKs.

**Runtime:** `sageo.connectors.gsc.call_tool`  
**Scope:** `https://www.googleapis.com/auth/webmasters.readonly`  
**Env (P1):** `GSC_CLIENT_EMAIL`, `GSC_PRIVATE_KEY`, `GSC_PROPERTY_URL`

## Tools

| Tool | Role |
| --- | --- |
| `gsc_search_analytics_query` | Search Analytics performance rows |
| `gsc_url_inspect` | URL Inspection index status |
| `gsc_sitemaps_list` | List submitted sitemaps |

## Failures → NHV

Missing env refuses start with `missing_credentials`. Upstream failures map to
`auth_failed` | `rate_limited` | `timeout` | `upstream_error` | `empty_result`.
Evidence `source` is `gsc/<tool>`.

## Excluded

Sitemap submit/delete; sites add/delete. No write scopes through P5.

## Tests

Hermetic recorded HTTP under `tests/connectors/gsc/` — no live Google calls in
default pytest/CI.
