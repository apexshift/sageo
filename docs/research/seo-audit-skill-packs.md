# Research: Prior-art SEO audit skill packs

**Ticket:** [#34](https://github.com/apexshift/sageo/issues/34)  
**Branch:** `research/seo-audit-skill-packs`  
**Scope:** Open skill packs, agent skill libraries, and audit checklists (SEO / AIO / GEO–relevant) that should inform SageO’s P2 roster **naming** and **coverage gaps** — without copying proprietary playbooks. Research only; roster freeze is [#35](https://github.com/apexshift/sageo/issues/35).

**Product filter:** SageO Skills are atomic, one capability pillar each (`skills/<pillar-slug>/<name>/SKILL.md`), with Evidence on claims, white-hat only, no auto-publish, Human review gates where remediation is finalised. P1 template already locked: `skills/technical-foundation/schema-validator/`. P2 target: **12–15 Skills**, ≥2–3 per pillar. Seed ideas include crawl-issue extraction, CWV scoring, indexability, intent classification, answer-extractability, entity coverage, citation opportunities, severity×impact scoring, evidence packaging, local schema, citation consistency.

**Method:** Prefer primary sources (official engine docs, open-source `SKILL.md` repos with OSI licences, published checklists with cited sources, arXiv). Treat vendor marketing pages and unpaid agency “150-point” blogs as secondary pattern signals only — never as copy targets.

---

## 1. Landscape map (what exists)

Three useful prior-art layers:

| Layer | What it is | How SageO should use it |
| --- | --- | --- |
| **A. Open Agent Skill packs** | Public repos of `SKILL.md` (+ optional scripts) for Claude Code / Codex / Cursor | Naming conventions, atomic vs mega-skill cuts, script+LLM split |
| **B. Open audit checklists** | MIT/CC checklists for SEO, GEO/AEO, AI-search readiness | Coverage taxonomies and gap lists — paraphrase categories, do not paste item text |
| **C. Official engine/platform audits** | Google Search Central, Lighthouse SEO, Core Web Vitals / web.dev | Ground-truth eligibility checks and metric definitions for Technical Foundation |

Sources for layer A catalogue: [RankSpotAI/awesome-seo-agent-skills](https://github.com/RankSpotAI/awesome-seo-agent-skills) (CC0 curated index, hand-checked Sept 2026). Sources for layer C: [Google Search technical requirements](https://developers.google.com/search/docs/essentials/technical), [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [Optimizing for generative AI](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide), [Lighthouse SEO audits](https://developer.chrome.com/docs/lighthouse/seo/), [Web Vitals](https://web.dev/articles/vitals).

---

## 2. Open Agent Skill packs (primary)

### 2.1 Catalogue signal: awesome-seo-agent-skills

The RankSpot curated list groups packs into: official vendor skills, large multi-skill suites, technical auditing, GEO/AEO/AI visibility, content/keywords, framework-specific, and smaller packs. It also lists **ecosystem gaps** that remain weakly served even after the 2026 skill boom:

- Log-file analysis (which bots crawled what)
- Internal linking **at scale** (real link-graph mapping)
- Hreflang / international SEO (outside mega-suites)
- Migration and redirect mapping
- **Schema validation** against rich-result requirements (many packs *generate* JSON-LD; few *validate*)
- CMS-specific skills (Webflow, Ghost, Shopify, Framer)

Source: [awesome-seo-agent-skills README — Gaps worth filling](https://github.com/RankSpotAI/awesome-seo-agent-skills).

**SageO note:** P1’s `schema-validator` already occupies one named gap. P2 should not invent a second schema Skill unless scope is clearly split (e.g. page JSON-LD vs LocalBusiness / NAP consistency).

### 2.2 marketingskills/seo — “SEO Operator” (MIT)

Atomic, verb-ish **task nouns** organised as Diagnose → Act → Strategize. Representative skill directory names:

| Cluster | Example skill names |
| --- | --- |
| Diagnose | `traffic-decay-detector`, `keyword-opportunity-finder`, `technical-seo-triage`, `cannibalization-check`, `serp-authority-mark`, `competitor-serp-monitor` |
| Act | `content-refresh-brief`, `seo-content-brief`, `internal-link-builder`, `schema-fix-writer`, `title-meta-rewriter`, `client-report-writer` |
| Strategize | `seo-priority-score`, `content-moat-planner`, `refresh-vs-new-content`, `seo-growth-loop` |

Source: [marketingskills/seo README](https://github.com/marketingskills/seo).

**Takeaways for SageO naming:** kebab-case; outcome-of-the-check as noun (`*-detector`, `*-triage`, `*-check`, `*-scorer`/`*-score`); avoid a single mega `seo-audit` Skill that does everything. Prefer composing many small Skills (SageO Agents/Orchestrator own composition — P3/P4).

**Coverage caution:** Several Act skills write briefs, proposals, or CMS-facing copy. SageO ethics (white-hat, Human review before finalised remediation / live changes) means P2 should bias toward **diagnose + score + package Evidence**, not autopilot publish or paid-link workflows found elsewhere in the ecosystem.

### 2.3 JeffLi1993/seo-audit-skill — script + LLM two-layer (MIT)

Architecture worth mirroring for Technical Foundation Skills:

1. **Layer 1 — deterministic Python** → JSON (`check-site.py`, `check-page.py`, `check-schema.py`, `fetch-page.py`, optional `check-pagespeed.py`).
2. **Layer 2 — LLM** only on fields flagged `llm_review_required` (intent alignment, content quality, expected `@type`).

Coverage buckets in the report model: site checks (robots, sitemap, 404/soft-404, canonicalization, hreflang, schema, E-E-A-T trust pages) + page checks (TDK, H1, headings, word count, internal links, robots meta) + optional PageSpeed/Lighthouse + priority actions with Evidence → Impact → Fix.

Source: [JeffLi1993/seo-audit-skill README](https://github.com/JeffLi1993/seo-audit-skill).

**Takeaways:** Split mega-audits into SageO Skills that match script boundaries where possible (`indexability-checker`, `crawl-issue-extractor`, `cwv-scorer`, existing `schema-validator`). Keep semantic judgment Skills separate (`intent-classifier`, `answer-extractability`).

### 2.4 AgriciDaniel/claude-seo — large suite naming (MIT)

Sub-skill folder names observed under `skills/` (prefix-heavy):

`seo-audit`, `seo-technical`, `seo-page`, `seo-schema`, `seo-sitemap`, `seo-content`, `seo-content-brief`, `seo-cluster`, `seo-backlinks`, `seo-competitor-pages`, `seo-local`, `seo-maps`, `seo-geo`, `seo-hreflang`, `seo-ecommerce`, `seo-images`, …

Source: GitHub contents listing for [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo).

**Takeaways:** The `seo-` prefix is redundant for SageO because pillar path already scopes capability (`skills/technical-foundation/...`). Prefer **pillar-local names** without outcome-pillar prefixes (`seo-`, `aio-`, `geo-`). Declare `primary_outcome` in Skill metadata instead (locked on master [#9](https://github.com/apexshift/sageo/issues/9) / [#4](https://github.com/apexshift/sageo/issues/4)).

### 2.5 Other open packs (signal only)

| Pack | Licence | Signal |
| --- | --- | --- |
| [Suganthan-Mohanadasan/tech-seo-audit-skill](https://github.com/Suganthan-Mohanadasan/tech-seo-audit-skill) | MIT | Crawl-CSV ingestion → 10-category analysis → **business-impact** priority spreadsheet (severity alone is not enough) |
| [Cited-io/ai-seo-geo-checklist](https://github.com/Cited-io/ai-seo-geo-checklist) (`skills/ai-seo-geo-audit`) | MIT | Checklist IDs (T/E/C/O/L/M) + agent skill; separates search crawlers vs training crawlers; evidence-bearing pass/warn/fail |
| [ashleytheash/seo-agent-skill](https://github.com/ashleytheash/seo-agent-skill) | unclear / none | `gsc-seo-prioritizer` naming pattern for Measurement pillar |
| [agharsallah/seo-engine-skills](https://github.com/agharsallah/seo-engine-skills) | unclear / none | Rules directory + Low/Med/High severity; deterministic claim |
| [MYehia565/google-seo-agent-skills](https://github.com/MYehia565/google-seo-agent-skills) | NOASSERTION | Lifecycle commands (discover → scope → fix → verify → review → ship) — maps to SageO Human review gate before ship |
| [seranking/seo-skills](https://github.com/seranking/seo-skills) | MIT | Vendor MCP-tied; useful as connector-adjacent pattern for P3, not as Skill copy |

**Licence hygiene (from RankSpot):** repos with **no licence file** are not free to copy despite README claims. SageO should cite category patterns only from OSI-licensed or official docs when borrowing structure.

---

## 3. Open audit checklists (SEO / AIO / GEO)

### 3.1 searchsolved/search-audit-kit — Google docs → checklists (primary-aligned)

Restructures **official Google Search Central** pages into 16 checklists / 667 items + MCP server. Checklist titles that map cleanly to SageO pillars:

| Checklist (kit) | Likely SageO pillar |
| --- | --- |
| Technical SEO, Search Essentials, JavaScript SEO, Mobile-First, Structured Data, Page Experience / CWV | Technical Foundation |
| Helpful Content, AI Optimization, Featured Snippets–adjacent | Content & Answer Quality |
| Links, Spam Policies | Authority & Trust |
| Debug Traffic Drops | Measurement & Prioritisation |
| International SEO | Local / Geographic (reach) + Technical |
| Ecommerce (specialty) | defer / optional later |

Source: [searchsolved/search-audit-kit README](https://github.com/searchsolved/search-audit-kit). Underlying Google sources linked per guide (e.g. [AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)).

**Use:** Coverage inventory against official Google guidance — not a Skill dump. SageO Skills should implement *narrow* checks with Evidence, not re-host 667 checklist rows.

### 3.2 Cited-io AI SEO / GEO / AEO checklist (MIT) — six sections

Stable IDs useful as a **coverage rubric** (not Skill names):

1. **Technical access (T*)** — robots.txt; allow AI **search** crawlers vs deliberate training-crawler policy; CDN/bot walls; rendering; sitemaps; IndexNow; llms.txt as optional/info  
2. **Entity and identity (E*)** — Organization schema, `sameAs`, NAP consistency, About, author bios  
3. **Content (C*)** — answer-first openings, one question per page, evidence-backed claims, comparisons/tables, freshness, anti–scaled-content-abuse  
4. **Off-site (O*)** — citation source lists, reviews, roundups, Reddit/YouTube authenticity, digital PR, no link schemes  
5. **Local (L*)** — GBP / Bing Places / Apple Business; LocalBusiness schema; NAP match  
6. **Measurement (M*)** — fixed prompt sets, multi-engine multi-run, mention vs citation, controls, change log, GSC generative reports, AI referral segments  

Source: [Cited-io/ai-seo-geo-checklist CHECKLIST.md](https://github.com/Cited-io/ai-seo-geo-checklist/blob/main/CHECKLIST.md). Aligns with Google’s stance that generative AI features are still SEO ([AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)) while adding other engines’ crawler docs.

### 3.3 Aflore-fr/aflore-geo-resources — 50-point GEO checklist

Five scored sections: Technical foundation (incl. `llms.txt`, AI bots in robots.txt, SSR), Schema.org types, Content structure (FAQ, TL;DR, tables, citations), Off-site retrieval coverage, Co-citation strategy.

Source: [Aflore CHECKLIST.md](https://github.com/Aflore-fr/aflore-geo-resources/blob/main/CHECKLIST.md).

**Caution:** Some items are agency practice (Wikipedia/Wikidata goals, “50 FAQ questions”) — mark as practice, not engine law. Useful for **entity coverage**, **citation opportunities**, and **answer-extractability** seed ideas.

### 3.4 henu-wang/geo-scoring-methodology — weighted 11 checks

Weighted dimensions include AI crawl access, structured data, llms.txt, content structure, meta tags, HTTP headers, sitemap, plus authority/E-E-A-T-oriented checks. Shows a **scored readiness** pattern for Measurement pillar (`severity × impact` / weighted score Skills).

Source: [geo-scoring-methodology README](https://github.com/henu-wang/geo-scoring-methodology).

### 3.5 Academic GEO baseline

Aggarwal et al., **GEO: Generative Engine Optimization**, arXiv:2311.09735 (KDD 2024): black-box visibility framework; content interventions (citations, statistics, quotations) improve visibility; keyword stuffing harms. Informs Content & Answer Quality Skills (`answer-extractability`, evidence-in-content) and Measurement visibility metrics — not a skill pack.

Source: [arXiv:2311.09735](https://arxiv.org/abs/2311.09735).

### 3.6 Explicitly out of scope for copying

- Ahrefs / Semrush / Moz **paid** audit methodologies and proprietary issue taxonomies (Moz publishes a free downloadable sheet — treat as secondary pattern only; do not import wording).  
- Agency “80/150-point” blog checklists without OSI licence or primary citations.  
- Skills that **buy backlinks**, mass-publish, or auto-submit without a human gate (seen in some ecosystem packs) — incompatible with SageO ethics.

---

## 4. Official engine / platform audit primitives

### 4.1 Google Search eligibility (minimum technical bar)

Google indexes only if: (1) Googlebot isn’t blocked, (2) HTTP 200, (3) indexable content. Indexing still not guaranteed.

Source: [Google Search technical requirements](https://developers.google.com/search/docs/essentials/technical).

Maps directly to an **`indexability-checker`** (or similarly named) Technical Foundation Skill — distinct from full crawl triage.

### 4.2 Lighthouse SEO category (open source)

Default SEO audits (from Lighthouse `default-config.js`): `is-crawlable`, `http-status-code`, `robots-txt`, `crawlable-anchors`, `document-title`, `meta-description`, `link-text`, `image-alt`, `hreflang`, `canonical`, plus unscored manual `structured-data`.

Sources: [Lighthouse default-config.js](https://github.com/GoogleChrome/lighthouse/blob/main/core/config/default-config.js); [Chrome SEO audits docs](https://developer.chrome.com/docs/lighthouse/seo/).

**Takeaway:** Lighthouse SEO is a **thin** page-level floor — necessary but far from a full technical or GEO audit. SageO should not treat “Lighthouse SEO 100” as roster completeness.

### 4.3 Core Web Vitals

Stable CWV: **LCP** ≤ 2.5s, **INP** ≤ 200ms, **CLS** ≤ 0.1, assessed at 75th percentile (field). Lab tools approximate; INP needs field/interaction.

Source: [web.dev Web Vitals](https://web.dev/articles/vitals).

Maps to seed **`cwv-scorer`** under Technical Foundation (or Measurement if field-only aggregation via CrUX/GSC — decide at grilling). Prefer field Evidence when connectors exist (P3); lab Evidence must be labelled as lab.

### 4.4 Local

Google documents LocalBusiness structured data and Business Profile guidance; Cited checklist L* items cite [LocalBusiness structured data](https://developers.google.com/search/docs/appearance/structured-data/local-business) and GBP guidelines. Supports seed **`local-schema`** + **`citation-consistency`** (NAP) under Local / Geographic.

---

## 5. Naming patterns that fit SageO

| Pattern | Examples in the wild | SageO guidance |
| --- | --- | --- |
| kebab-case task noun | `traffic-decay-detector`, `cannibalization-check` | **Preferred** for Skill directory `name` (must match Agent Skills spec) |
| Role of check | `*-checker`, `*-extractor`, `*-scorer`, `*-classifier`, `*-packager` | Match seed list; keep one verb-family per Skill |
| Mega audit | `seo-audit`, `seo-audit-full` | **Avoid** as a P2 library Skill; compose via Agent later |
| Outcome prefix | `seo-technical`, `geo-audit` | **Avoid** in folder name; use `primary_outcome` metadata |
| Severity-only | Low/Med/High issue tags | Incomplete alone — prefer **severity × impact** (or effort) like tech-seo-audit-skill / `seo-priority-score` |
| Checklist IDs | T2, E1, C4 | Useful inside references/, not as Skill names |

Agent Skills open format constraints (name = directory, lowercase hyphenated) already researched in [docs/research/agent-skill-packaging.md](./agent-skill-packaging.md) and locked on master layout/metadata tickets.

---

## 6. Coverage matrix: seeds × pillars × prior art

| Seed / candidate | Pillar | Prior-art support | Gap vs ecosystem |
| --- | --- | --- | --- |
| `schema-validator` (P1) | Technical Foundation | JeffLi `check-schema`; RankSpot gap “schema validation”; Lighthouse manual structured-data | **Differentiator already claimed** |
| crawl issue extractor | Technical Foundation | `technical-seo-triage`; tech-seo-audit-skill crawl categories; Search Audit Kit technical checklist | Common — differentiate with Evidence contract + NHV |
| indexability checker | Technical Foundation | Google technical requirements; JeffLi robots/canonical/noindex; Lighthouse `is-crawlable` | Common — keep **narrow** (eligibility), not full audit |
| CWV scorer | Technical Foundation | web.dev CWV; JeffLi pagespeed script; Page Experience checklists | Common — label lab vs field |
| intent classifier | Content & Answer Quality | marketingskills briefs / opportunity finder; GEO paper query–content fit | Less standardised as a named skill — good SageO atomic |
| answer-extractability | Content & Answer Quality | Cited C*; Aflore content structure; GEO paper passage visibility | **AIO/GEO differentiator**; rare as atomic open skill |
| entity coverage | Authority & Trust / Content | Cited E*; Aflore schema/entity; Organization/`sameAs` | Strong GEO overlap — name carefully vs Local |
| citation opportunities | Authority & Trust | Cited O*; Aflore co-citation; RankSpot GEO packs | Differentiator; keep white-hat (no link buying) |
| citation consistency (NAP) | Local / Geographic | Cited L6; LocalBusiness docs | Clear Local Skill |
| local schema | Local / Geographic | Google LocalBusiness; Aflore LocalBusiness template | Complements P1 schema-validator (page-generic vs local types) |
| severity × impact scoring | Measurement & Prioritisation | `seo-priority-score`; tech-seo-audit business-impact phase; GEO weighted scores | Cross-cutting — one Skill that scores Evidence from others |
| evidence packaging | Measurement & Prioritisation | JeffLi Evidence→Impact→Fix; SageO Evidence contract (#5) | **SageO-native**; few packs enforce structured Evidence |
| (implied) AI crawler access | Technical Foundation | Cited T*; geo-scoring AI crawl access | Often folded into mega-audit — candidate atomic Skill |
| (implied) internal-link graph | Authority or Technical | RankSpot gap; `internal-link-builder` (act-oriented) | Gap if P2 wants diagnose-only `internal-link-auditor` |
| (implied) hreflang | Technical / Local-reach | RankSpot gap; claude-seo `seo-hreflang`; JeffLi i18n | Coverage gap if roster skips international |

---

## 7. What prior art implies for P2 shape

1. **Atomic Skills beat mega-audits** for a library that Agents will compose. Prior art that ships one `seo-audit` skill forces prompts to load huge checklists; SageO’s progressive-disclosure + pillar folders favour 12–15 focused names.  
2. **Script + LLM split** is proven for technical checks; Measurement/Content Skills may be Markdown-only in v1 where judgment dominates — consistent with hybrid layout (#8).  
3. **GEO/AIO is under-represented as atomics** relative to classical technical SEO. Prior art either bolts “GEO” onto a mega pack or publishes checklists without Skills. SageO seed ideas (`answer-extractability`, `entity coverage`, `citation opportunities`) close a real gap **if** named without using GEO as a folder (GEO = Outcome pillar per glossary).  
4. **Schema validation is an advertised ecosystem hole** — keep `schema-validator` central; add `local-schema` only if LocalBusiness/NAP scope is distinct.  
5. **Prioritisation must combine severity and impact** (and optionally effort/confidence) — one Measurement Skill should consume Evidence from others rather than each Skill inventing its own score dialect.  
6. **Do not copy** proprietary issue IDs, paid-tool taxonomies, or autopilot/link-buy skills. Cite Google / web.dev / OSI checklists for *what* to cover; invent SageO names and Evidence shapes.  
7. **Connectors stay out of Skill bodies** — packs that embed DataForSEO/GSC SDKs are P3 MCP territory per master connector policy (#6).

---

## Implications for P2 roster

Use this section as input to grilling ticket [#35](https://github.com/apexshift/sageo/issues/35).

**Naming rules (recommended):** kebab-case task nouns; no `seo-`/`aio-`/`geo-` folder prefixes; prefer `*-checker` / `*-extractor` / `*-scorer` / `*-classifier` / `*-packager`; one concern per Skill; declare `primary_outcome` in metadata.

**Coverage targets (map seeds → ≥2–3 Skills per pillar):**

| Pillar | Strong prior-art-backed candidates (illustrative, not frozen) |
| --- | --- |
| Technical Foundation | `schema-validator` (P1), `indexability-checker`, `crawl-issue-extractor`, `cwv-scorer`, optional `ai-crawler-access` or `hreflang-checker` |
| Content & Answer Quality | `intent-classifier`, `answer-extractability`, optional content-freshness / helpful-content slice |
| Authority & Trust | `entity-coverage`, `citation-opportunities` (white-hat only) |
| Measurement & Prioritisation | `severity-impact-scorer` (name TBD), `evidence-packager` |
| Local / Geographic | `local-schema`, `citation-consistency` (NAP), optional GBP-readiness later with connectors |

**Roster grilling should resolve:** exact 12–15 names; whether AI-crawler access and hreflang are in P2 or deferred; lab vs field ownership for CWV; whether `entity-coverage` lives under Authority vs Content; scripts vs Markdown-only for each; and explicit **non-goals** (no mega `seo-audit`, no link-buying, no auto-publish Act skills in P2).

**Differentiator to preserve:** structured Evidence + NHV + Human review gates + pillar organisation — prior art rarely enforces these as first-class contracts.
