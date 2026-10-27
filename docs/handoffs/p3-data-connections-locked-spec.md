# P3 Data connections & audit orchestrator — locked spec handoff

**Status:** Locked for `/to-spec` → implement  
**Phase map:** [Phase map: P3 Data connections & audit orchestrator](https://github.com/apexshift/sageo/issues/42)  
**Master map:** [Master map: SageO five-phase bootstrap](https://github.com/apexshift/sageo/issues/1)  
**Accept on master:** [Accept P3 locked spec](https://github.com/apexshift/sageo/issues/20)  
**Depends on:** [Accept P2 locked spec](https://github.com/apexshift/sageo/issues/18) / [P2 handoff](https://github.com/apexshift/sageo/blob/handoff/p2-core-skill-library-locked-spec/docs/handoffs/p2-core-skill-library-locked-spec.md) (and P1 foundation)

This handoff is the single linked artifact required by [Define phase exit criteria for locked specs](https://github.com/apexshift/sageo/issues/13) for P3. It does **not** implement MCP servers or Orchestrator runtime; it specifies contracts.

## Inherit

All master Decisions on [#1](https://github.com/apexshift/sageo/issues/1), especially connector policy [#6](https://github.com/apexshift/sageo/issues/6), Orchestrator vs Agent [#11](https://github.com/apexshift/sageo/issues/11), Evidence/logging [#5](https://github.com/apexshift/sageo/issues/5), test ramp [#12](https://github.com/apexshift/sageo/issues/12). Domain: `GLOSSARY.md`. P1 `.env.example` keys unchanged.

## Exit criteria checklist

| Criterion | Satisfied by |
| --- | --- |
| GSC/GA4/crawl-SERP vendor + stub shapes | Vendor [#44](https://github.com/apexshift/sageo/issues/44); GSC [#45](https://github.com/apexshift/sageo/issues/45); GA4 [#46](https://github.com/apexshift/sageo/issues/46); crawl/SERP [#47](https://github.com/apexshift/sageo/issues/47) |
| Full `ORCHESTRATOR.md` (routing, prioritisation, gate enforcement) | [#48](https://github.com/apexshift/sageo/issues/48) |
| Connector MCP contracts | [#45](https://github.com/apexshift/sageo/issues/45)–[#47](https://github.com/apexshift/sageo/issues/47) |
| Orchestrator tests | [#49](https://github.com/apexshift/sageo/issues/49) |

## Crawl/SERP vendor

**DataForSEO** — hybrid On-Page + SERP, PAYG, REST Basic auth.

| Env key | Mapping |
| --- | --- |
| `CRAWL_SERP_API_KEY` | `login:password` → Base64 Basic |
| `CRAWL_SERP_BASE_URL` | `https://api.dataforseo.com` |

SageO owns a thin MCP pack with stable tool names (not wholesale vendor MCP). Skills stay SDK-free.

Research: [`docs/research/crawl-serp-connector-vendors.md`](https://github.com/apexshift/sageo/blob/research/crawl-serp-connector-vendors/docs/research/crawl-serp-connector-vendors.md).

## Connector MCP stubs (read-only)

Common: missing env → refuse start + NHV `missing_credentials`. Failures → NHV with `verification_reason` ∈ `missing_credentials` | `auth_failed` | `rate_limited` | `timeout` | `upstream_error` | `empty_result`. No invented metrics. No write scopes through P5.

### GSC — `connectors/gsc/`

Auth: `GSC_CLIENT_EMAIL`, `GSC_PRIVATE_KEY`, `GSC_PROPERTY_URL`; scope `webmasters.readonly`.

| Tool | Role |
| --- | --- |
| `gsc_search_analytics_query` | Search Analytics performance rows |
| `gsc_url_inspect` | URL Inspection index status |
| `gsc_sitemaps_list` | List submitted sitemaps |

Excluded: sitemap submit/delete; sites add/delete.

### GA4 — `connectors/ga4/`

Auth: `GA4_PROPERTY_ID`, `GA4_CREDENTIALS_JSON`; scope `analytics.readonly`; property `properties/{id}`.

| Tool | Role |
| --- | --- |
| `ga4_run_report` | Data API `runReport` |
| `ga4_get_metadata` | Available dimensions/metrics |

Excluded: realtime; Admin mutations; Measurement Protocol.

### Crawl/SERP — `connectors/crawl-serp/`

Auth: `CRAWL_SERP_*` as above. Task-based crawl: start → poll summary → pages.

| Tool | Role |
| --- | --- |
| `crawl_start_task` | On-Page `task_post` → `task_id` |
| `crawl_site_summary` | On-Page summary / `crawl_progress` |
| `crawl_page_issues` | On-Page pages + checks |
| `serp_google_organic` | Google organic + common SERP elements |

Excluded: Lighthouse-as-separate surface; AI Summary billed endpoints; vendor MCP passthrough.

## ORCHESTRATOR.md contract

Path: `orchestrator/ORCHESTRATOR.md`. Frontmatter: `name`, `description`, `metadata.version`. No `skills:` list.

| Section | Locked policy |
| --- | --- |
| **Purpose** | Route/prioritise/sequence Agents; enforce Human review gates; never call Skills directly |
| **Routing** | Intent → `primary_outcome` (+ Reach) + Agent When-to-use; Agents never route to Agents; unknown → ask-human / NHV |
| **Prioritisation** | Severity×impact when scored, else FIFO; gates never skipped for cost |
| **Multi-agent** | Sequential default; shared Run directory; thin audit placeholders: Technical → Content/AIO → Measurement; explicit fan-out only when independent |
| **Human review** | Agents declare gates; Orchestrator owns the stop until Decision log approval |
| **Decision logging** | Orchestrator entries for route/priority/schedule/gate; append-only under `runs/<id>/` |
| **Inputs/Outputs** | Run goal + property refs + outcome → `run_id`, Agent statuses, Evidence refs, gate state |

Concrete Agent identities wait for P4.

## Test strategy (P3 bar)

### Connectors — `tests/connectors/<pack>/`

```text
tests/connectors/<pack>/   # gsc | ga4 | crawl-serp
  http/                    # recorded request/response JSON
  expected/
  test_*.py
```

Per pack: happy-path contract test per locked tool; ≥1 NHV failure case; **no live network** in default pytest/CI.

### Orchestrator — `tests/orchestrator/`

Fake in-process Agents (When-to-use, outcome, optional scores, `human_review_gate`). Green proves: routing, severity×impact vs FIFO, gate stop/resume, thin audit pipeline with three placeholders.

Non-goals: live vendor calls; P4 Agent goldens; P5 e2e.

## Deliverables implement must create

```text
connectors/gsc/                 # MCP pack + README/contract
connectors/ga4/
connectors/crawl-serp/
orchestrator/ORCHESTRATOR.md    # prose filling locked sections
tests/connectors/gsc/
tests/connectors/ga4/
tests/connectors/crawl-serp/
tests/orchestrator/
```

(Plus any shared connector HTTP/fixture helpers under the package as implement chooses.)

## Next steps

1. `/to-spec` against this handoff → implement P3 connectors + Orchestrator.  
2. Close [Accept P3 locked spec](https://github.com/apexshift/sageo/issues/20) on the master map when the handoff is accepted.  
3. Then [Chart phase map P4](https://github.com/apexshift/sageo/issues/21).

## Out of scope for P3 implement

- Reference Agents / real `AGENT.md` identities (P4)  
- CI / packaging (P5)  
- Live API calls in default CI  
- Write scopes / auto-publish  
- Replacing P1/P2 Skill goldens (still required)
