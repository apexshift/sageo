# P2 Core skill library — locked spec handoff

**Status:** Locked for `/to-spec` → implement  
**Phase map:** [Phase map: P2 Core skill library](https://github.com/apexshift/sageo/issues/33)  
**Master map:** [Master map: SageO five-phase bootstrap](https://github.com/apexshift/sageo/issues/1)  
**Accept on master:** [Accept P2 locked spec](https://github.com/apexshift/sageo/issues/18)  
**Depends on:** [Accept P1 locked spec](https://github.com/apexshift/sageo/issues/16) / [P1 handoff](https://github.com/apexshift/sageo/blob/handoff/p1-foundation-locked-spec/docs/handoffs/p1-foundation-locked-spec.md)

This handoff is the single linked artifact required by [Define phase exit criteria for locked specs](https://github.com/apexshift/sageo/issues/13) for P2. It does **not** implement Skills; it specifies the library contracts.

## Inherit

All master Decisions on [#1](https://github.com/apexshift/sageo/issues/1) and P1 handoff (layout, Skill metadata contract, Evidence, test harness, ethics). Domain: `GLOSSARY.md`.

## Exit criteria checklist

| Criterion | Satisfied by |
| --- | --- |
| Named roster of 12–15 Skills across five pillars | [Freeze P2 Skill roster](https://github.com/apexshift/sageo/issues/35) — **14 Skills** |
| Each Skill’s `SKILL.md` contract fields filled | [Assign P2 Skill contract fields](https://github.com/apexshift/sageo/issues/36) |
| Golden path per Skill | [Define P2 golden fixture strategy](https://github.com/apexshift/sageo/issues/37) |
| Implement priority order | [Freeze P2 implement priority order](https://github.com/apexshift/sageo/issues/38) |

## Roster (14)

| Pillar | `name` | Purpose |
| --- | --- | --- |
| technical-foundation | `schema-validator` | Validate schema/structured data on a page fixture → Evidence (P1) |
| technical-foundation | `indexability-checker` | Assess indexability signals from page/headers fixtures |
| technical-foundation | `crawl-issue-extractor` | Extract/classify crawl issues from crawl/log fixtures |
| technical-foundation | `cwv-scorer` | Score Core Web Vitals vs lab/fixture thresholds |
| content-answer-quality | `intent-classifier` | Classify query/page intent |
| content-answer-quality | `answer-extractability-scorer` | Score extractability for answer engines |
| content-answer-quality | `entity-coverage-checker` | Check topical/entity coverage for answer quality |
| authority-trust | `citation-opportunity-identifier` | White-hat citation/mention opportunities |
| authority-trust | `mention-sentiment-screener` | Screen brand mentions for sentiment/risk |
| measurement-prioritisation | `severity-impact-scorer` | Score issues by severity × impact |
| measurement-prioritisation | `evidence-packager` | Package Evidence into a review-ready bundle |
| local-geographic | `local-schema-checker` | Validate local business structured data |
| local-geographic | `citation-consistency-checker` | Check NAP/citation consistency |
| local-geographic | `gbp-profile-auditor` | Audit GBP completeness/quality from fixtures |

**Non-goals:** no mega `seo-audit`; no link-buying/spam; no auto-publish Act Skills; deferred `ai-crawler-access-checker`, `hreflang-checker`.

## Contract fields

| `name` | `primary_outcome` | `secondary_outcomes` | `evidence_requirement` | `human_review_gate` | `connectors` |
| --- | --- | --- | --- | --- | --- |
| `schema-validator` | SEO | AIO, GEO | full | not_required | — |
| `indexability-checker` | SEO | — | full | not_required | — |
| `crawl-issue-extractor` | SEO | — | full | not_required | `crawl_serp` |
| `cwv-scorer` | SEO | — | full | not_required | — |
| `intent-classifier` | AIO | SEO | full | not_required | — |
| `answer-extractability-scorer` | AIO | SEO, GEO | full | not_required | — |
| `entity-coverage-checker` | AIO | SEO, GEO | full | not_required | — |
| `citation-opportunity-identifier` | SEO | AIO, GEO | full | not_required | — |
| `mention-sentiment-screener` | SEO | AIO | full | not_required | — |
| `severity-impact-scorer` | SEO | AIO, GEO | full | not_required | — |
| `evidence-packager` | SEO | AIO, GEO | partial | not_required | — |
| `local-schema-checker` | SEO | AIO, GEO | full | not_required | — |
| `citation-consistency-checker` | SEO | — | full | not_required | — |
| `gbp-profile-auditor` | SEO | AIO | full | not_required | — |

`version` starts at `0.1.0` at implement. Required `SKILL.md` body sections per master Skill metadata contract.

## Golden fixture strategy

Path: `tests/skills/<pillar>/<name>/{input/,expected.json,evidence.schema.json,README.md}`  
≥1 happy path; prefer +1 edge/NHV. No live APIs; mock `crawl_serp`.

| Class | Skills |
| --- | --- |
| `page-html` | schema-validator, local-schema-checker, answer-extractability-scorer, entity-coverage-checker |
| `headers-html` | indexability-checker |
| `crawl-log` | crawl-issue-extractor |
| `lab-metrics` | cwv-scorer |
| `query-page` | intent-classifier |
| `opportunity-corpus` | citation-opportunity-identifier, mention-sentiment-screener |
| `issue-list` | severity-impact-scorer |
| `evidence-bundle` | evidence-packager |
| `listings-nap` | citation-consistency-checker |
| `gbp-fixture` | gbp-profile-auditor |

## Implement priority (waves)

1. **W1:** `schema-validator` (polish to full P2 golden layout)  
2. **W2:** `indexability-checker`, `cwv-scorer`, `local-schema-checker`, `answer-extractability-scorer`, `entity-coverage-checker`  
3. **W3:** `intent-classifier`, `citation-opportunity-identifier`, `mention-sentiment-screener`  
4. **W4:** `citation-consistency-checker`, `gbp-profile-auditor`  
5. **W5:** `crawl-issue-extractor` → `severity-impact-scorer` → `evidence-packager` (last)

Rules: fixture-only before connector Skills; producers before Measurement consumers; `evidence-packager` last.

## Research input

[docs/research/seo-audit-skill-packs.md](https://github.com/apexshift/sageo/blob/research/seo-audit-skill-packs/docs/research/seo-audit-skill-packs.md) ([#34](https://github.com/apexshift/sageo/issues/34)).

## Next steps

1. `/to-spec` against this handoff → implement P2 Skills by wave.  
2. Close [Accept P2 locked spec](https://github.com/apexshift/sageo/issues/18) when master accepts this handoff.  
3. Then [Chart phase map P3](https://github.com/apexshift/sageo/issues/19).

## Out of scope for P2 implement

- Connector vendors/MCP stubs (P3)  
- Orchestrator / Agents (P3–P4)  
- CI (P5)  
- Live API calls; auto-publish
