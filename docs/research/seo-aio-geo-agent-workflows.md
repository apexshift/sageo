# Research: SEO / AIO / GEO agent workflow patterns

**Ticket:** [#53](https://github.com/apexshift/sageo/issues/53)  
**Branch:** `research/seo-aio-geo-agent-workflows`  
**Scope:** Credible reference patterns for composing SEO / AIO / GEO (generative) audit-style **Agent workflows** that compose atomic Skills (not mega-audits), declare Human review gates, and fit SageO’s Agent contract ([#10](https://github.com/apexshift/sageo/issues/10)). Research only; four-Agent roster freeze is [#54](https://github.com/apexshift/sageo/issues/54).

**Product filter:** Agents compose Skills across capability pillars; Orchestrator routes and enforces gates ([#11](https://github.com/apexshift/sageo/issues/11)); Agents never route to Agents; P3 thin audit placeholders are Technical findings → Content/AIO → Measurement/Evidence; P2 roster = 14 atomic Skills; GEO = generative engine optimisation (not geography); Reach = local | national | global; white-hat only; no auto-publish; Human review before live-site change or finalised remediation.

**Method:** Prefer primary sources (Google Search Central / Business Profile docs, Agent Skills / Anthropic composition guidance, arXiv GEO, OSI-licensed checklists with cited sources). Treat vendor marketing and unpaid “150-point” blogs as secondary pattern signals only.

---

## 1. What “fit” means for SageO Agents

| Constraint | Implication for workflow design |
| --- | --- |
| Atomic Skills, not mega-audits | One Agent = ordered Skill composition + gates; never a single `seo-audit` Skill that does everything ([#34](https://github.com/apexshift/sageo/issues/34) research) |
| Agent contract (#10) | `AGENT.md`: `primary_outcome`, `skills`, `human_review_gate`, `cost_model`; body **Skills invoked** (order/conditions) + **Human review points** |
| Orchestrator seam (#11) | Agent runs one workflow; Orchestrator sequences Agents and owns the hard stop at gates |
| P3 placeholders | Three audit slots already named; P4 picks a deliberate fourth |
| Outcome vs Reach | SEO / AIO / GEO frame `primary_outcome`; Local is a capability pillar **and** a Reach scope — do not fold Local into GEO |

---

## 2. Common workflow stages (prior art)

Across classical SEO audits, Google’s generative-AI guidance, GEO/AEO checklists, and open agent-skill packs, audit-style work converges on a **gated sequence**: access first, then structure/content, then authority/local (when in scope), then score/package, then human decision.

| Stage | Question answered | Typical outputs | SageO Skill affinity |
| --- | --- | --- | --- |
| **1. Access / crawl / index** | Can engines fetch and index the pages that matter? | Blockers, non-indexables, crawl issues | `indexability-checker`, `crawl-issue-extractor` |
| **2. Technical structure** | Is markup, schema, and page experience clear? | Schema/CWV findings | `schema-validator`, `cwv-scorer` |
| **3. Content / answer quality** | Does each page match intent and yield extractable answers? | Intent map, extractability scores, entity gaps | `intent-classifier`, `answer-extractability-scorer`, `entity-coverage-checker` |
| **4. Authority / trust** | Are entities clear and citation opportunities white-hat? | Opportunity lists, mention risk | `citation-opportunity-identifier`, `mention-sentiment-screener` |
| **5. Local / presence** (Reach=local) | Are GBP, LocalBusiness schema, and NAP consistent? | Profile/NAP/schema findings | `gbp-profile-auditor`, `local-schema-checker`, `citation-consistency-checker` |
| **6. Measurement / packaging** | What matters most, and what Evidence is review-ready? | Severity×impact ranks, Evidence bundle | `severity-impact-scorer`, `evidence-packager` |
| **7. Human review** | Approve remediation direction before live change? | Decision-log approval | Gate declared by Agent; stop owned by Orchestrator |

**Order matters.** Practitioner GEO checklists and technical-audit guides repeatedly put crawl/access before content: a blocked page cannot be cited or ranked. Measurement is last among diagnose stages so it consumes Evidence from producers. Human review sits **after** packaging and **before** any Act/remediation that could touch a live site — matching SageO ethics.

Sources for the stage shape: [Google technical requirements](https://developers.google.com/search/docs/essentials/technical); [Google AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide); [Cited-io AI SEO/GEO checklist](https://github.com/Cited-io/ai-seo-geo-checklist/blob/main/CHECKLIST.md) (MIT); [marketingskills/seo](https://github.com/marketingskills/seo) Diagnose → Act → Strategize; Anthropic [Building effective agents](https://www.anthropic.com/research/building-effective-agents) (prompt chaining + programmatic gates).

---

## 3. How prior art groups the work

### 3.1 Official engine framing (primary)

**Google Search — generative AI features.** Foundational SEO remains the base: valuable non-commodity content, clear technical structure, and (where relevant) local/ecommerce details; measure generative visibility in Search Console. Explicit mythbust: no special `llms.txt` / “chunking” / AEO-hack requirement for Google Search. Local Business Profiles and Merchant Center are called out as first-class for AI responses.

Source: [Optimizing for generative AI features](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide); [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features).

**Implication:** A Content/AIO Agent and a Technical Agent are both justified; Local is a separate optimisation surface, not a GEO synonym.

### 3.2 Six-section AI SEO / GEO checklist (high-trust open)

Cited-io groups checks as **T → E → C → O → L → M**:

| Section | Focus | Maps toward SageO |
| --- | --- | --- |
| **T** Technical access | robots, AI search vs training crawlers, CDN/WAF, indexability, HTML-first content, sitemaps | Technical Agent |
| **E** Entity & identity | Organization schema, `sameAs`, NAP consistency, About | Content/AIO (+ Authority Skills) |
| **C** Content | Answer-first openings, one question/page, evidence-backed claims | Content/AIO Agent |
| **O** Off-site | Citation sources, reviews, roundups, digital PR (no link schemes) | Authority Skills inside Content/AIO or Measurement consumers |
| **L** Local | GBP, Bing/Apple places, LocalBusiness, NAP match | **Local Reach Agent** |
| **M** Measurement | Fixed prompt sets, mention vs citation, GSC generative reports | Measurement/Evidence Agent |

Source: [Cited-io/ai-seo-geo-checklist CHECKLIST.md](https://github.com/Cited-io/ai-seo-geo-checklist/blob/main/CHECKLIST.md).

### 3.3 Open agent-skill operators (composition pattern)

**marketingskills/seo — SEO Operator (MIT)** clusters skills into **Diagnose → Act → Strategize**, not one mega-audit. Diagnose owns triage/decay/opportunity; Act writes briefs/schema proposals/reports; Strategize owns priority scoring and growth loops.

Source: [marketingskills/seo README](https://github.com/marketingskills/seo).

**SageO cut:** P2 Skills are Diagnose (+ score/package) only. Agents should stay in Diagnose → Prioritise → Package → **Human gate**. Act/Strategize that mutate live sites or finalise remediation plans stay behind the gate (and largely out of P4 reference Agents).

### 3.4 Academic GEO baseline

Aggarwal et al. model generative engines as retrieval + synthesis and show content interventions (citations, statistics, quotations) improve visibility; keyword stuffing harms. Measurement is **visibility in generated answers**, not only SERP position.

Source: [arXiv:2311.09735](https://arxiv.org/abs/2311.09735) (KDD 2024).

**Implication:** Content/AIO Agent should emphasise extractability and evidence-in-content Skills; Measurement Agent should be able to consume AIO/GEO-oriented Evidence, not only classic SEO severity.

### 3.5 GEO practitioner audit layers (secondary, consistent signal)

Independent GEO audit write-ups converge on stacked layers such as: **retrieval/access → extraction/quotable content → trust/entity → displacement/measurement**. Order matches Cited T→C→E/O→M. Useful as corroboration; prefer Cited + Google + arXiv when naming SageO stages.

### 3.6 Local / GBP (primary)

Google’s Business Profile guidelines: real-world name (no keyword stuffing), accurate address/service area, few specific categories, one profile per location, honest hours/phone/website. Local ranking factors documented as relevance, distance, prominence. LocalBusiness structured data is a separate Google Search surface.

Sources: [Guidelines for representing your business on Google](https://support.google.com/business/answer/3038177); [LocalBusiness structured data](https://developers.google.com/search/docs/appearance/structured-data/local-business); [How Google ranks local results](https://support.google.com/business/answer/7091).

**Implication:** Local work is a coherent **workflow** (profile + schema + NAP), not a leftover Technical check — strong case for a fourth Agent when Reach=local.

### 3.7 Agent composition & Human gates (primary for contract fit)

| Pattern | Source | SageO reading |
| --- | --- | --- |
| Skills = composable procedural units; progressive disclosure | [Agent Skills spec](https://agentskills.io/specification); [Anthropic Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | Agents list Skills; load only what the workflow needs |
| Workflows = predefined paths with programmatic checkpoints (“gates”) | [Building effective agents](https://www.anthropic.com/research/building-effective-agents) | Agent declares Human review points; Orchestrator enforces |
| Prefer skills-in-one-loop over deep subagent trees for many enterprise tasks; hard limits in harness | [When to fold subagents](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) | Aligns with “Agents never route to Agents”; Orchestrator sequences sibling Agents |
| Defined roles + human verification early | [Building effective human-agent teams](https://claude.com/resources/articles/building-effective-human-agent-teams) | Roles = four reference Agents; gates before remediation |

---

## 4. Mapping groups → SageO pillars & P3 placeholders

| Prior-art group | Capability pillars | P3 placeholder | Outcome bias |
| --- | --- | --- | --- |
| Technical / access / CWV / schema | Technical Foundation | **Technical findings** | SEO primary; AIO/GEO eligibility secondary |
| Content / answer / entity coverage | Content & Answer Quality (+ Authority for opportunities) | **Content/AIO** | AIO primary; GEO + SEO secondary |
| Off-site / mentions (diagnose only) | Authority & Trust | Feeds Content/AIO **or** Measurement | SEO/AIO |
| Local / GBP / NAP / LocalBusiness | Local / Geographic | *(none in P3 — candidate fourth)* | SEO primary; Reach=local |
| Severity × impact / Evidence bundle | Measurement & Prioritisation | **Measurement/Evidence** | Cross-cutting (SEO/AIO/GEO) |

P3 already sequences Technical → Content/AIO → Measurement as the default multi-agent audit. The missing first-class surface in that chain is **Local Reach**, which has three P2 Skills and official Google surfaces, and must not be confused with Outcome-pillar GEO.

---

## 5. Human review gate patterns

Credible patterns that fit `#10` / `#11`:

1. **Declare, don’t soft-warn.** Anthropic workflow “gates” are programmatic checkpoints; SageO Human review gates are hard stops before live-site change or finalised remediation (`GLOSSARY.md`).
2. **Two layers.** Agent: when in the workflow a gate is required (`human_review_gate` + **Human review points**). Orchestrator: nothing proceeds past a required gate without Decision-log approval.
3. **Where gates sit in audit workflows.** After Evidence is packaged and prioritised; before any Act skill, CMS write, GBP edit proposal marked final, or remediation plan marked approved. Diagnose Agents may set `human_review_gate: required` when their **Outputs** include a remediation plan; pure finding Agents may use `not_required` on intermediate runs if the Measurement Agent owns the final package gate — roster grilling (#54/#55) should pick one consistent policy.
4. **Avoid Act-without-gate.** Open packs that auto-publish or buy links are incompatible; marketingskills Act cluster is a pattern for *briefs and proposals*, not for SageO to ship ungated.

---

## 6. Recommended shortlist: four Agent shapes for #54

Recommend **exactly four** shapes. Names below are **illustrative kebab-case** for grilling — #54 locks final `name` / one-liners / `primary_outcome`.

### Shape A — Technical findings Agent

| Field | Recommendation |
| --- | --- |
| Illustrative `name` | `technical-findings` |
| Purpose | Diagnose crawl, indexability, schema, and CWV blockers that prevent SEO (and generative eligibility). |
| `primary_outcome` | `SEO` (optional secondary: AIO, GEO — eligibility only) |
| Aligns with | P3 placeholder **Technical findings** |
| Likely Skills (order sketch) | `crawl-issue-extractor` → `indexability-checker` → `schema-validator` → `cwv-scorer` |
| Human review | Usually after findings if this Agent emits a fix list alone; often deferred to Measurement package when run in the default trio |
| Cost drivers | Crawl/SERP connector calls + page fixtures; mostly deterministic Skills |

### Shape B — Content / AIO Agent

| Field | Recommendation |
| --- | --- |
| Illustrative `name` | `content-aio` |
| Purpose | Diagnose intent fit, answer extractability, entity coverage, and white-hat citation opportunities for answer/generative surfaces. |
| `primary_outcome` | `AIO` (secondary: `GEO`, `SEO`) |
| Aligns with | P3 placeholder **Content/AIO**; carries **GEO outcome** work without naming the Agent “geo-*” |
| Likely Skills (order sketch) | `intent-classifier` → `answer-extractability-scorer` → `entity-coverage-checker` → `citation-opportunity-identifier` |
| Human review | Before any content-remediation brief is marked final |
| Cost drivers | LLM-heavy judgment Skills; tokens_and_connector_calls if SERP samples used later |

### Shape C — Measurement / Evidence Agent

| Field | Recommendation |
| --- | --- |
| Illustrative `name` | `measurement-evidence` |
| Purpose | Score issue severity × impact, screen mention risk when relevant, and package Evidence into a review-ready bundle for Human decision. |
| `primary_outcome` | `SEO` (secondary: AIO, GEO — cross-cutting) |
| Aligns with | P3 placeholder **Measurement/Evidence** |
| Likely Skills (order sketch) | `mention-sentiment-screener` (optional/conditional) → `severity-impact-scorer` → `evidence-packager` |
| Human review | **`required`** when Outputs finalise a remediation priority pack — natural system-wide gate before Act |
| Cost drivers | Mostly tokens on packaged Evidence; connector-light if consuming prior run artifacts |

### Shape D — Local Reach Agent *(deliberate fourth)*

| Field | Recommendation |
| --- | --- |
| Illustrative `name` | `local-reach` |
| Purpose | Diagnose Google Business Profile quality, LocalBusiness schema, and NAP/citation consistency for **Reach=local** properties. |
| `primary_outcome` | `SEO` (optional secondary AIO — local in AI responses per Google) |
| Reach | Declares **local**; Orchestrator routes when intent/Reach is local or multi-location |
| Aligns with | Cited **L\*** section; Google GBP + LocalBusiness docs; fills the P3 gap |
| Likely Skills (order sketch) | `gbp-profile-auditor` → `local-schema-checker` → `citation-consistency-checker` |
| Human review | **`required`** before any GBP/listing change recommendations are finalised |
| Cost drivers | Fixture-first in P4 goldens; later read-only connectors if added |

### Why Local Reach over remediation-planning as the fourth

| Candidate | Pros | Cons for P4 reference set |
| --- | --- | --- |
| **Local Reach** | Three P2 Skills otherwise orphaned from P3 placeholders; official Google surfaces; Reach is a SageO first-class axis; Orchestrator can skip when Reach≠local | Narrower for national/global-only runs (acceptable — Orchestrator omits) |
| Remediation-planning | Useful Strategize/Act pattern (priority → brief → approve) | Blurs into Measurement’s package gate; risks Act-without-Skill inventory; duplicates `severity-impact-scorer` + `evidence-packager`; easier to add later as a fifth Agent than to strand Local |

**Decision recommendation for #54:** lock Shape D as Local Reach; keep remediation planning as a possible **future** Agent after P4, not one of the four reference Agents.

---

## 7. Default multi-agent sequence (Orchestrator)

Fits P3 policy and #11 (Agents never route to Agents):

```text
technical-findings  →  content-aio  →  [local-reach if Reach=local]  →  measurement-evidence
                                                                         └─ Human review gate
```

- Sequential default; shared `runs/<id>/`.
- Fan-out only when independent (e.g. Local Reach parallel to Content/AIO after Technical clears access blockers).
- Measurement last so it consumes upstream Evidence.
- GEO **outcome** work lives primarily in Content/AIO (+ Measurement consuming its Evidence), not in a separate “GEO Agent” that would confuse Outcome with Local.

---

## 8. Skill coverage matrix (illustrative)

| P2 Skill | A Technical | B Content/AIO | C Measurement | D Local Reach |
| --- | --- | --- | --- | --- |
| `schema-validator` | ● | | | |
| `indexability-checker` | ● | | | |
| `crawl-issue-extractor` | ● | | | |
| `cwv-scorer` | ● | | | |
| `intent-classifier` | | ● | | |
| `answer-extractability-scorer` | | ● | | |
| `entity-coverage-checker` | | ● | | |
| `citation-opportunity-identifier` | | ● | | |
| `mention-sentiment-screener` | | ○ | ● | |
| `severity-impact-scorer` | | | ● | |
| `evidence-packager` | | | ● | |
| `local-schema-checker` | | | | ● |
| `citation-consistency-checker` | | | | ● |
| `gbp-profile-auditor` | | | | ● |

● = primary composition; ○ = optional alternate home (grilling may pin `mention-sentiment-screener` to C only).

All 14 Skills appear at least once; no mega-audit Skill required.

---

## 9. Anti-patterns to reject

1. **One mega `seo-audit` / `geo-audit` Agent** that inlines checklist text instead of composing Skills — fights progressive disclosure and P2 design.
2. **GEO-named Agent that means local geography** — glossary collision; use Local Reach + Outcome metadata instead.
3. **Agent-to-Agent routing** inside an AGENT.md procedure — violates #11.
4. **Ungated Act** (CMS publish, GBP edit, link acquisition) in reference Agents.
5. **Copying proprietary issue taxonomies** from Ahrefs/Semrush/Moz paid audits — cite Google / OSI checklists for *categories*, invent SageO Evidence shapes.
6. **Treating Lighthouse SEO 100 as workflow completeness** — thin page floor only ([Lighthouse SEO audits](https://developer.chrome.com/docs/lighthouse/seo/)).

---

## 10. Implications for #54 (roster grilling)

Use this section as input to [#54](https://github.com/apexshift/sageo/issues/54).

**Lock:**

1. Four identities matching shapes **A–D** (final kebab-case `name`s).
2. One-line purposes and `primary_outcome` (+ Reach note on D; secondary outcomes on B/C).
3. Explicit non-goal: no remediation-planning Agent in the P4 reference four; no Agent named for Outcome GEO as if it were Local.

**Defer to later P4 tickets:**

- Exact Skill lists/order and gate wording → contracts ticket (#55).
- Golden workflow fixtures → goldens ticket (#56).
- Handoff / locked spec → #57.

**Differentiator to preserve:** atomic Skill composition + declared Human review points + Orchestrator-enforced stops + Evidence packaging — prior art rarely ships all four as contracts.

---

## Sources (selected)

### Primary / official

- [Google: Optimizing for generative AI features](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- [Google: AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)
- [Google: Search technical requirements](https://developers.google.com/search/docs/essentials/technical)
- [Google: LocalBusiness structured data](https://developers.google.com/search/docs/appearance/structured-data/local-business)
- [Google Business Profile representation guidelines](https://support.google.com/business/answer/3038177)
- [Google: How local results rank](https://support.google.com/business/answer/7091)
- [web.dev Web Vitals](https://web.dev/articles/vitals)
- [Chrome Lighthouse SEO audits](https://developer.chrome.com/docs/lighthouse/seo/)
- [Agent Skills specification](https://agentskills.io/specification)
- [Anthropic: Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Anthropic: Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- Aggarwal et al., *GEO: Generative Engine Optimization*, [arXiv:2311.09735](https://arxiv.org/abs/2311.09735)

### High-trust open practitioner

- [Cited-io/ai-seo-geo-checklist](https://github.com/Cited-io/ai-seo-geo-checklist) (MIT)
- [marketingskills/seo](https://github.com/marketingskills/seo) (MIT) — Diagnose / Act / Strategize
- Prior SageO research: [seo-audit-skill-packs.md](./seo-audit-skill-packs.md) ([#34](https://github.com/apexshift/sageo/issues/34)); [agent-skill-packaging.md](./agent-skill-packaging.md) ([#2](https://github.com/apexshift/sageo/issues/2))

### Secondary signal only

- GEO audit layer blogs (retrieval → extraction → trust → measurement) — corroborate order; do not copy proprietary scoring.
- Agency GBP “N-point” checklists — corroborate Local as its own workflow; prefer Google guidelines for rules.
