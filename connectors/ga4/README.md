# GA4 Connector pack

SageO-owned read-only MCP surface for Google Analytics 4 Data API. Skills call
these tool names; they do not embed Google SDKs.

**Runtime:** `sageo.connectors.ga4.call_tool`  
**Scope:** `https://www.googleapis.com/auth/analytics.readonly`  
**Env (P1):** `GA4_PROPERTY_ID`, `GA4_CREDENTIALS_JSON`  
**Property:** `properties/{GA4_PROPERTY_ID}`

## Tools

| Tool | Role |
| --- | --- |
| `ga4_run_report` | Data API `runReport` |
| `ga4_get_metadata` | Available dimensions and metrics |

## Failures → NHV

Missing env refuses start with `missing_credentials`. Upstream failures map to
`auth_failed` | `rate_limited` | `timeout` | `upstream_error` | `empty_result`.
Evidence `source` is `ga4/<tool>`.

## Excluded

Realtime reports; Admin API mutations; Measurement Protocol / data-collection
writes. No write scopes through P5.

## Tests

Hermetic recorded HTTP under `tests/connectors/ga4/` — no live Google calls in
default pytest/CI.
