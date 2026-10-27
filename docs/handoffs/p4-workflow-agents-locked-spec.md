# P4 Workflow agents — locked spec handoff

**Status:** Locked for `/to-spec` → implement  
**Phase map:** [Phase map: P4 Workflow agents](https://github.com/apexshift/sageo/issues/52)  
**Master map:** [Master map: SageO five-phase bootstrap](https://github.com/apexshift/sageo/issues/1)  
**Accept on master:** [Accept P4 locked spec](https://github.com/apexshift/sageo/issues/22)  
**Depends on:** [Accept P3 locked spec](https://github.com/apexshift/sageo/issues/20) / [P3 handoff](https://github.com/apexshift/sageo/blob/handoff/p3-data-connections-locked-spec/docs/handoffs/p3-data-connections-locked-spec.md); P2 Skill roster

This handoff is the single linked artifact required by [Define phase exit criteria for locked specs](https://github.com/apexshift/sageo/issues/13) for P4. It does **not** implement Agent runtimes; it specifies the four reference Agents.

## Inherit

Master Decisions on [#1](https://github.com/apexshift/sageo/issues/1), especially Agent contract [#10](https://github.com/apexshift/sageo/issues/10), Orchestrator vs Agent [#11](https://github.com/apexshift/sageo/issues/11), test ramp [#12](https://github.com/apexshift/sageo/issues/12). Domain: `GLOSSARY.md`. P2 Skill roster; P3 Orchestrator routes these Agents (Agents never route to Agents).

## Exit criteria checklist

| Criterion | Satisfied by |
| --- | --- |
| Four reference Agents fully specified | Identities [#54](https://github.com/apexshift/sageo/issues/54); Skill lists/gates/cost [#55](https://github.com/apexshift/sageo/issues/55) |
| Goldens | [#56](https://github.com/apexshift/sageo/issues/56) |
| Skill lists | [#55](https://github.com/apexshift/sageo/issues/55) — all 14 P2 Skills covered |

## Four reference Agents

| `name` | Purpose | `primary_outcome` | Reach / notes |
| --- | --- | --- | --- |
| `technical-findings` | Crawl, indexability, schema, CWV blockers | `SEO` | Optional secondary AIO/GEO (eligibility) |
| `content-aio` | Intent, extractability, entity coverage, white-hat citation opportunities | `AIO` | Secondary GEO, SEO; carries GEO **outcome** (not geography) |
| `measurement-evidence` | Severity×impact, optional mention screen, Evidence package | `SEO` | Secondary AIO, GEO; system package gate |
| `local-reach` | GBP, LocalBusiness schema, NAP consistency | `SEO` | **Reach=local**; Orchestrator omits when Reach≠local |

**Rejected for P4 four:** remediation-planning Agent; GEO-named Agent meaning geography.

Research: [`docs/research/seo-aio-geo-agent-workflows.md`](https://github.com/apexshift/sageo/blob/research/seo-aio-geo-agent-workflows/docs/research/seo-aio-geo-agent-workflows.md).

## Contracts per Agent

### `technical-findings`
- **skills (order):** `crawl-issue-extractor`, `indexability-checker`, `schema-validator`, `cwv-scorer`
- **human_review_gate:** `not_required`
- **cost_model:** `tokens_and_connector_calls`
- **Human review points:** Findings only; Measurement owns package gate. Pause only on blocking NHV.
- **Conditions:** crawl → indexability → schema → CWV; skip CWV if no lab-metrics input.

### `content-aio`
- **skills (order):** `intent-classifier`, `answer-extractability-scorer`, `entity-coverage-checker`, `citation-opportunity-identifier`
- **human_review_gate:** `required`
- **cost_model:** `tokens_and_connector_calls`
- **Human review points:** Before any content-remediation brief is marked final. White-hat only.
- **Conditions:** Intent first; extractability + entity; citation opportunities when authority inputs exist.

### `measurement-evidence`
- **skills (order):** `mention-sentiment-screener` (conditional), `severity-impact-scorer`, `evidence-packager`
- **human_review_gate:** `required`
- **cost_model:** `tokens_only`
- **Human review points:** System package gate before prioritised Evidence / remediation priority pack approval. Orchestrator owns hard stop.
- **Conditions:** Mention screener only when corpus present; always severity×impact then package.

### `local-reach`
- **skills (order):** `gbp-profile-auditor`, `local-schema-checker`, `citation-consistency-checker`
- **human_review_gate:** `required`
- **cost_model:** `tokens_and_connector_calls`
- **Human review points:** Before any GBP/listing change recommendations are finalised.
- **Conditions:** Route when Reach=local; GBP → local schema → NAP.

Frontmatter/body sections follow Agent metadata contract [#10](https://github.com/apexshift/sageo/issues/10). Path pattern: `agents/<name>/AGENT.md`.

## Golden workflow strategy

```text
tests/agents/<agent-name>/
  fixtures/
  expected/
  test_golden.py
```

- Skills **stubbed** (order + canned Evidence/outputs).
- Assert Skill order, Decision log fields, gate pause/resume when `required`.
- `technical-findings` completes without required gate pause.
- ≥1 happy path per Agent; no live APIs.

## Default Orchestrator sequence (from P3)

When Reach is not local: `technical-findings` → `content-aio` → `measurement-evidence`.  
When Reach=local: include `local-reach` (typically after technical or in parallel only if Orchestrator explicitly fans out independent work).

## Deliverables implement must create

```text
agents/technical-findings/AGENT.md
agents/content-aio/AGENT.md
agents/measurement-evidence/AGENT.md
agents/local-reach/AGENT.md
tests/agents/technical-findings/
tests/agents/content-aio/
tests/agents/measurement-evidence/
tests/agents/local-reach/
```

## Next steps

1. `/to-spec` against this handoff → implement P4 Agents.  
2. Close [Accept P4 locked spec](https://github.com/apexshift/sageo/issues/22) when the handoff is accepted.  
3. Then [Chart phase map P5](https://github.com/apexshift/sageo/issues/23).

## Out of scope for P4 implement

- P5 e2e / CI / packaging / metrics helper  
- Live Skill execution inside Agent goldens (stubs OK)  
- Remediation-planning Agent  
- Auto-publish / write scopes  
- Changing P3 Orchestrator routing policy
