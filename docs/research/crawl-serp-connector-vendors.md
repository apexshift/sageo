# Research: Crawl / SERP connector vendor options

**Ticket:** [#43](https://github.com/apexshift/sageo/issues/43)  
**Branch:** `research/crawl-serp-connector-vendors`  
**Scope:** Credible crawl or SERP-insights vendors (or open APIs) that fit SageO’s P3 **one crawl/SERP connector class** — MCP-pack-shaped, read-only, env-credentialed tools that Skills can call without embedding vendor SDKs. Research only; vendor lock is [#44](https://github.com/apexshift/sageo/issues/44).

**Product filter:** Master connector policy ([#6](https://github.com/apexshift/sageo/issues/6)): GSC and GA4 are already separate in-scope connectors; this class is the **third**. Connectors = MCP server packs, separate from Skills. Credentials via env only (`.env.example` already has `CRAWL_SERP_API_KEY`, `CRAWL_SERP_BASE_URL`). Read-only through P5. Failures → NHV Evidence (`missing_credentials` | `auth_failed` | `rate_limited` | `timeout` | `upstream_error` | `empty_result`). Skills must not embed vendor SDKs.

**Method:** Prefer primary sources (official API docs, pricing pages, first-party MCP READMEs). Treat comparison blogs as secondary signal only.

---

## 1. What “fit” means for this class

SageO needs **one** abstract crawl/SERP connector. Ideal coverage for Skills such as `crawl-issue-extractor`, SERP-feature checks, and Evidence packaging:

| Need | Why |
| --- | --- |
| **Crawl / on-page issues** | Indexability, redirects, duplicates, broken resources, on-page checks — Technical Foundation Skills |
| **SERP features** | Organic positions, PAA, local pack, AI Overviews / rich results — Measurement / Content / Local Skills |
| **HTTP + env auth** | Maps to `CRAWL_SERP_*`; no desktop licence tied to a human workstation for CI mocks |
| **MCP-packable** | Thin HTTP client in `connectors/`; optional first-party MCP is a bonus, not a requirement |
| **Read-only** | No mutations of client sites; crawl/SERP fetch is observational |
| **Failure taxonomy** | Clear HTTP/auth/rate-limit errors → NHV Evidence without inventing metrics |

**Hybrid** vendors (crawl **and** SERP under one account/API family) best match “one class.” SERP-only or crawl-only vendors remain valid if #44 deliberately narrows the class.

---

## 2. Vendor scorecards (primary sources)

### 2.1 DataForSEO — hybrid (crawl + SERP) — **top recommendation**

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth** | HTTP Basic: dashboard API **login** + generated **password** in `Authorization: Basic base64(login:password)`. No OAuth dance. | [docs.dataforseo.com/v3/auth](https://docs.dataforseo.com/v3/auth/) |
| **Base URL** | `https://api.dataforseo.com/` (v3 REST) | Auth + On-Page / SERP overviews |
| **Crawl data** | **On-Page API**: task POST crawl → Summary (issue overview, `crawl_progress`, domain/ssl info), Pages, Non-indexable, Redirect Chains, Duplicate Tags/Content, Links, Resources, Waterfall, Instant Pages, optional browser rendering / CWV. | [On-Page overview](https://docs.dataforseo.com/v3/on_page/overview), [Summary](https://docs.dataforseo.com/v3/on_page/summary/) |
| **SERP data** | **SERP API**: Google (and Bing, Yahoo, etc.); Regular / Advanced / HTML; Live or Standard queue; organic + rich SERP elements; AI Summary / Screenshot helpers. | [SERP overview](https://docs.dataforseo.com/v3/serp/overview/) |
| **Rate limits** | Help center: general **~10,000 requests/minute**; **30** simultaneous requests for many endpoints; On-Page Instant Pages up to 10k/min with ≤20 tasks/request. Live SERP recommended steadier pacing. | [Rate limits help](https://dataforseo.com/help-center/rate-limits-and-request-limits), On-Page overview limits |
| **Pricing posture** | **Pay-as-you-go**, no subscription; **$50** minimum top-up; balance never expires; **$1** trial credit + Sandbox. On-Page from **$0.00015**/crawled page; Google SERP from **$0.0006**/SERP (Standard cheaper than Live; depth adds cost). | [Pricing](https://dataforseo.com/pricing), [On-Page pricing](https://dataforseo.com/pricing/on-page), [SERP pricing](https://dataforseo.com/pricing/serp), [SERP cost explained](https://dataforseo.com/help-center/serp-api-cost-explained) |
| **MCP / fit** | **Official MCP**: [`dataforseo/mcp-server-typescript`](https://github.com/dataforseo/mcp-server-typescript) / `npx dataforseo-mcp-server`; env `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` (aliases vary by README version); hosted `https://mcp.dataforseo.com/v3/mcp`. Tools include docs browse + authenticated `api_request`. SageO should still ship its **own** thin MCP pack with **stable tool names** (not vendor MCP wholesale) so Skills stay vendor-swappable. | [MCP product page](https://dataforseo.com/model-context-protocol), [GitHub README](https://github.com/dataforseo/mcp-server-typescript) |
| **Env mapping** | Single `CRAWL_SERP_API_KEY` is awkward for Basic login+password. Options for #44: (a) store `login:password` in `CRAWL_SERP_API_KEY` and Base64 in the pack; (b) document `CRAWL_SERP_API_KEY` as password + add `CRAWL_SERP_LOGIN` later; (c) keep abstract and map in connector config. `CRAWL_SERP_BASE_URL` → `https://api.dataforseo.com`. | Policy #6 + P1 `.env.example` |

**Fit:** Best **single-vendor** coverage of both crawl-issue and SERP-feature shapes under one PAYG account. REST + Basic auth is MCP-friendly without SDKs. Official MCP proves agentability; SageO still owns tool schemas.

---

### 2.2 SerpApi — SERP-focused (mature + official MCP)

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth** | `api_key` query parameter (and MCP Bearer / path-key). | [Google Search API](https://serpapi.com/search-api) |
| **Data shape** | Structured Google (and 80+ engines) JSON: organic, local, knowledge graph, PAA, related searches, AI-oriented `output=md`, etc. **No site crawl / on-page issue API.** | Same + [pricing](https://serpapi.com/pricing) |
| **Rate limits** | Plan **throughput/hour** (e.g. Free 50/hr, Developer 1,000/hr, Production 3,000/hr). Cached searches free / not counted. | [Pricing](https://serpapi.com/pricing) |
| **Pricing posture** | Monthly subscription; Free **250**/mo; Starter **$25**/1k; Developer **$75**/5k; Production **$150**/15k; scales to Cloud tiers. Month-to-month, cancel anytime. | [Pricing](https://serpapi.com/pricing) |
| **MCP / fit** | **Official hosted MCP** `https://mcp.serpapi.com/{API_KEY}/mcp` (or Bearer); open-source [serpapi/serpapi-mcp](https://github.com/serpapi/serpapi-mcp). Clean single-key → `CRAWL_SERP_API_KEY`. | [serpapi.com/mcp](https://serpapi.com/mcp) |

**Fit:** Excellent if #44 narrows the class to **SERP insights only** and accepts crawl issues via GSC + local/script Skills. Weak as the sole vendor if Technical Foundation crawl-issue Skills need a third-party crawler.

---

### 2.3 Serper.dev — SERP-focused (cheap / Google-only)

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth** | `X-API-KEY` header on `https://google.serper.dev/...`. | Product/docs examples on [serper.dev](https://serper.dev) (homepage API demos) |
| **Data shape** | Fast Google SERP JSON: organic, knowledgeGraph, peopleAlsoAsk, relatedSearches; Images/News/Maps/Places/etc. endpoints. **No crawl audit.** | Homepage response samples |
| **Pricing posture** | Prepaid credits; **2,500 free** queries; marketed as low $/1k Google SERP (credit packs). | Homepage “2,500 free queries” |
| **MCP / fit** | No first-party MCP found in primary materials; trivial to wrap as HTTP MCP. Maps cleanly to `CRAWL_SERP_API_KEY` + `CRAWL_SERP_BASE_URL=https://google.serper.dev`. | — |

**Fit:** Strong **cost** alternative for Google SERP-only Skills. Weaker documentation depth / legal posture vs SerpApi; still no crawl.

---

### 2.4 Lumar (formerly DeepCrawl) — crawl-focused (enterprise GraphQL)

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth** | Service account **`x-api-key`**, or user-key → session token in **`x-auth-token`** (30-day sessions). | [Authentication](https://api-docs.lumar.io/docs/graphql/authentication) |
| **Base URL** | `https://api.lumar.io/graphql` | [API docs home](https://api-docs.lumar.io/) |
| **Data shape** | Project/crawl GraphQL: health scores, segments, crawl URL metrics, SEO report categories — **enterprise website intelligence**, not SERP. | Docs + [Segments](https://api-docs.lumar.io/docs/graphql/segments/) |
| **Pricing posture** | Enterprise / sales-led (public marketing historically ~tens of k$/yr; confirm with sales — not self-serve PAYG like DataForSEO). | Vendor positioning on [lumar.io/api](https://www.lumar.io/api/) |
| **MCP / fit** | No official MCP located. GraphQL is packable but heavier than REST for a thin P3 stub. | — |

**Fit:** Best-in-class **crawl** depth for large orgs; poor bootstrap fit (cost, GraphQL complexity, no SERP, no MCP). Keep as enterprise escape hatch, not P3 default.

---

### 2.5 Screaming Frog SEO Spider MCP — crawl-focused (local licence)

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth / deploy** | **Paid licence** desktop app as MCP server (stdio or loopback Streamable HTTP). Not a hosted multi-tenant API. | [MCP Server guide](https://www.screamingfrog.co.uk/guides/mcp-server/), [v24 blog](https://www.screamingfrog.co.uk/blog/seo-spider-24/) |
| **Data shape** | Rich crawl tools: `sf_crawl`, reports, bulk exports, SEO element filters (Indexability, Redirects, Titles, …), URL info — industry-standard issue taxonomies. | Same guide (API tool list) |
| **Pricing posture** | Annual SEO Spider licence (paid feature; free tier has no MCP). | Guide: “paid licence feature only” |
| **MCP / fit** | **Native MCP** — closest “crawl MCP” in the market. **Misaligned** with SageO env-hosted connector policy (`CRAWL_SERP_BASE_URL` + CI mocks): requires local Spider install, licensed human machine, filesystem/node tools. | Guide |

**Fit:** Outstanding for practitioner desktop workflows; **not** the P3 cloud connector class. Note as optional future “local adapter,” not the locked vendor for `connectors/crawl-serp`.

---

### 2.6 Firecrawl — content crawl (LLM markdown, weak SEO-issue taxonomy)

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth** | `Authorization: Bearer fc-…` | [API introduction](https://docs.firecrawl.dev/api-reference/introduction) |
| **Data shape** | Scrape/Crawl/Map → markdown/HTML/metadata for LLM ingestion; Search credits for web search. **Not** an SEO issue auditor (no non-indexable / redirect-chain / duplicate-title product surface comparable to On-Page or SF). | [Crawl feature](https://docs.firecrawl.dev/features/crawl), [Pricing](https://www.firecrawl.dev/pricing) |
| **Rate limits** | Plan RPM + concurrent browsers (e.g. Free 10/min scrape, 2/min crawl; Hobby higher). | [Rate limits](https://docs.firecrawl.dev/rate-limits) |
| **Pricing posture** | Free 1k credits/mo; Hobby ~$19/mo; credit = page for basic scrape/crawl. | [Pricing](https://www.firecrawl.dev/pricing) |
| **MCP / fit** | Vendor invests in agent/MCP onboarding; still wrong **data shape** for SageO crawl-issue Skills. | Docs |

**Fit:** Useful if SageO needed “fetch page as markdown”; **out of scope** as the crawl/SERP insights class.

---

### 2.7 Bright Data SERP API — SERP at proxy scale

| Dimension | Facts | Sources |
| --- | --- | --- |
| **Auth** | Bearer API key; requests need a configured **zone**. | [Introduction](https://docs.brightdata.com/products/serp-api/introduction), [Authentication](https://docs.brightdata.com/api-reference/authentication) |
| **Data shape** | SERP HTML/JSON/Markdown via unlocker-style pipeline; multi-engine. No On-Page crawl product in this class. | Same |
| **Rate limits** | Fair-use RPM (unfunded example **1,000 req/min**); 429 when exceeded. | [SERP rate limit](https://docs.brightdata.com/general/usage-monitoring/serp-rate-limit) |
| **Pricing posture** | Per **1,000 successful** requests; free monthly credit pool mentioned in quickstart; geared to volume/proxy ops. | [Pricing & billing](https://docs.brightdata.com/products/serp-api/pricing-and-billing), [Quickstart](https://docs.brightdata.com/products/serp-api/quickstart) |
| **MCP / fit** | HTTP-packable; zone+proxy mental model heavier than SerpApi/DataForSEO for a bootstrap stub. | — |

**Fit:** Viable SERP backend at scale; overkill and crawl-incomplete for P3 “one class.”

---

### 2.8 Other options (brief)

| Option | Why not shortlisted for P3 default | Primary pointer |
| --- | --- | --- |
| **Google Custom Search JSON API** | Programmable Search Engine; limited free quota / not full SERP feature parity for SEO audits | [Google PSE docs](https://developers.google.com/custom-search/v1/overview) |
| **Ahrefs / Semrush APIs** | Broad SEO suites; expensive seats; exceed “one crawl/SERP class”; Skills must not embed suite SDKs | Vendor developer portals |
| **Sitebulb** | Strong Hint UX; no comparable public hosted crawl API for env-credentialed MCP packs | Product site (no public API docs found for this use) |
| **Oxylabs / other scrapers** | Proxy/SERP infrastructure; similar trade-offs to Bright Data | Vendor docs |

---

## 3. Comparison matrix (at a glance)

| Vendor | Crawl issues | SERP features | Auth → env | Pricing glance | Official MCP | P3 fit |
| --- | --- | --- | --- | --- | --- | --- |
| **DataForSEO** | Yes (On-Page) | Yes (SERP API) | Basic login+pass (map carefully) | PAYG; cheap per page/SERP; $50 min | Yes | **Best hybrid** |
| **SerpApi** | No | Yes (deep) | API key | Sub from $25/mo | Yes | Best SERP-only |
| **Serper.dev** | No | Yes (Google) | API key | Cheap credits | No (wrap) | Budget SERP |
| **Lumar** | Yes (enterprise) | No | `x-api-key` | Enterprise | No | Later / enterprise |
| **Screaming Frog MCP** | Yes (local) | No | Licence + local app | ~annual licence | Yes (local) | Not hosted connector |
| **Firecrawl** | Content crawl ≠ SEO issues | Search lite | Bearer | Credit plans | Vendor MCP lean | Wrong shape |
| **Bright Data SERP** | No | Yes | Bearer + zone | Per 1k success | No | Scale SERP only |

---

## 4. MCP pack design notes (vendor-agnostic)

Regardless of #44’s pick, the SageO pack should:

1. **Expose stable tools** such as `crawl_site_summary`, `crawl_page_issues`, `serp_google_organic` (names illustrative) — **not** raw vendor path passthrough as the Skill contract.  
2. **Read credentials only from env**; refuse start + emit NHV Evidence on missing creds (policy #6).  
3. **Translate** 401→`auth_failed`, 429→`rate_limited`, timeouts→`timeout`, empty SERP/crawl→`empty_result`.  
4. **Keep Skills SDK-free** — `httpx`/`fetch` inside the connector pack only.  
5. **Mock in CI** (test policy #12); never call live vendors in default PR CI.  
6. Treat vendor-hosted MCP (DataForSEO, SerpApi, Screaming Frog) as **existence proofs**, not as the shipped `connectors/` implementation — SageO owns schemas and Evidence mapping.

---

## 5. Recommended shortlist for [#44](https://github.com/apexshift/sageo/issues/44)

Ordered recommendation:

1. **DataForSEO (top)** — Only researched vendor that cleanly covers **both** On-Page crawl issues and SERP features under one PAYG account, with REST + Basic auth and an official MCP. Accept env-mapping nuance for login+password vs single `CRAWL_SERP_API_KEY`.  
2. **SerpApi** — If #44 decides the class is **SERP-primary** (crawl deferred to GSC + scripted/local checks). Best docs, feature depth, hosted MCP, simple API key. Higher $/query than DataForSEO/Serper.  
3. **Serper.dev** — Budget Google-SERP alternative if cost dominates and multi-engine / legal shield matter less.  
4. **Lumar** — Crawl-only enterprise alternative if a future customer already standardises on Lumar; not bootstrap default.  
5. **Screaming Frog MCP** — Explicit **non-pick** for the hosted `CRAWL_SERP_*` connector; optional later local integration path.

**Defer-with-abstract-only?** Not warranted — DataForSEO (and SerpApi for SERP-narrow) are credible fits. Prefer locking a vendor (or locking “DataForSEO with abstract tool names”) rather than shipping an unbacked stub forever.

**Trade-off summary for grilling:**

| Path | Gain | Cost |
| --- | --- | --- |
| Hybrid DataForSEO | One vendor for crawl-issue + SERP Skills | Map Basic auth to env keys; learn task POST/GET async patterns |
| SERP SerpApi | Simplest key + richest SERP/MCP | No On-Page crawl; subscription floor |
| SERP Serper | Lowest Google SERP cost | Google-only; wrap your own MCP; thinner primary docs |
| Crawl Lumar / SF | Deep crawl taxonomies | No SERP; enterprise or local-only — breaks “one hosted class” |

---

## Implications for #44 (pick vendor)

Lock **one** of:

- **A. DataForSEO** as the P3 crawl/SERP vendor — recommend **A**. Document env mapping (`CRAWL_SERP_BASE_URL=https://api.dataforseo.com`, credential encoding strategy) and which On-Page + SERP endpoints the MCP stub must cover for P3 Skills.  
- **B. SerpApi** if the map explicitly drops third-party crawl from the class.  
- **C. Abstract-only + mock** only if commercial/legal review blocks A/B (research does not currently justify this).

Out of scope for #44: implementing the MCP server, signing paid contracts beyond trial, or resolving GSC/GA4 contracts (#45–#50 grilling/tasks).
