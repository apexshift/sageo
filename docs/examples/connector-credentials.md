# Example: Connector credentials

Connectors are **read-only** MCP packs under `connectors/` (GSC, GA4,
crawl-serp). Skills consume Connector tools; they do not embed vendor SDKs.
Credentials come from **environment variables only** — never commit real
secrets.

## Placeholders: `.env.example`

1. Copy [`.env.example`](../../.env.example) to `.env` locally (`.env` is
   gitignored).
2. Fill only the vars you need for local Connector experiments.
3. Leave unused keys empty. Default `make ci` / pytest do **not** require
   production secrets; Connector tests use recorded HTTP fixtures.

Shipped packs:

- [`connectors/gsc/`](../../connectors/gsc/)
- [`connectors/ga4/`](../../connectors/ga4/)
- [`connectors/crawl-serp/`](../../connectors/crawl-serp/)

## Variable groups (from `.env.example`)

| Connector | Env vars (placeholders) |
| --- | --- |
| GSC | `GSC_CLIENT_EMAIL`, `GSC_PRIVATE_KEY`, `GSC_PROPERTY_URL` |
| GA4 | `GA4_PROPERTY_ID`, `GA4_CREDENTIALS_JSON` |
| crawl-serp | `CRAWL_SERP_API_KEY`, `CRAWL_SERP_BASE_URL` |

On auth failure, rate limit, or empty payloads, Skills/Connectors emit
Evidence with `confidence: needs_human_verification` and a
`verification_reason` — they must not invent metrics.

## Related

- Ethics / read-only policy:
  [`docs/ethical-accountability-policy.md`](../ethical-accountability-policy.md)
- Architecture Connectors layer: [`docs/architecture.md`](../architecture.md)
