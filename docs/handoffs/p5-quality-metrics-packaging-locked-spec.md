# P5 Quality, metrics & packaging — locked spec handoff

**Status:** Locked for `/to-spec` → implement  
**Phase map:** [Phase map: P5 Quality, metrics & packaging](https://github.com/apexshift/sageo/issues/59)  
**Master map:** [Master map: SageO five-phase bootstrap](https://github.com/apexshift/sageo/issues/1)  
**Accept on master:** [Accept P5 locked spec](https://github.com/apexshift/sageo/issues/24)  
**Depends on:** [Accept P4 locked spec](https://github.com/apexshift/sageo/issues/22) and prior phase handoffs

This handoff is the single linked artifact required by [Define phase exit criteria for locked specs](https://github.com/apexshift/sageo/issues/13) for P5. Accepting it on the master completes the five-phase bootstrap destination. It does **not** implement CI YAML or cut a release tag on the wayfinding map.

## Inherit

All master Decisions on [#1](https://github.com/apexshift/sageo/issues/1); P1–P4 handoffs; contribution posture [#7](https://github.com/apexshift/sageo/issues/7); test ramp [#12](https://github.com/apexshift/sageo/issues/12). Domain: `GLOSSARY.md`.

## Exit criteria checklist

| Criterion | Satisfied by |
| --- | --- |
| Metrics helper | [#60](https://github.com/apexshift/sageo/issues/60) |
| E2e workflow | [#61](https://github.com/apexshift/sageo/issues/61) |
| Packaging / CI | [#62](https://github.com/apexshift/sageo/issues/62) |
| Version sync | [#63](https://github.com/apexshift/sageo/issues/63) |
| Public-release checklist | [#64](https://github.com/apexshift/sageo/issues/64) |

## Metrics helper

- Shared package helper (library/CLI); optional Skill wrapper out of required scope.
- Reports **cost estimates** (from `cost_model` + usage stubs) and **Evidence completeness**.
- Artifact under Run directory; **no invented SEO ranking/traffic KPIs**.
- Tests: complete Evidence → pass; missing Evidence id → fail; cost section present.

## End-to-end golden

- Scenario: **national audit** — `technical-findings` → `content-aio` → `measurement-evidence` (Reach ≠ local).
- Skills stubbed; connectors mocked; no live APIs.
- Assert routing, Skill orders, Measurement gate pause/resume, Evidence/Decision logs, metrics helper report.
- Layout: `tests/e2e/national-audit/`.
- `local-reach` covered by P4 Agent goldens.

## Packaging and CI

- **Publish:** GitHub Release + installable Python package (`pyproject`); Skill/Agent/Orchestrator/Connector packs stay in-repo; MIT.
- **Actions (PR + default branch):** lint + contract lint + pytest.
- Hermetic: no live vendor/Google calls; default CI secret-free.

## Version sync

- **Component semver:** each Skill/Agent/Orchestrator `metadata.version` (independent; start `0.1.0`).
- **Product version:** package + GitHub Release tag.
- No lockstep across all `metadata.version`.
- Root `CHANGELOG.md` tracks product releases.

## Public-release CONTRIBUTING + checklist

### CONTRIBUTING outline
Timing (after first public tag); issues first; Skills + docs/fixes for outsiders; Agents/Orchestrator/Connectors maintainer-only; Skill contribution bar; ethics/LICENSE pointers.

### First public release checklist
CI green; metrics on e2e; CHANGELOG; versions; README/ethics/CONTRIBUTING; MIT; no secrets; no-hype review; then tag Release + package.

## Deliverables implement must create

```text
# shared metrics helper (package module + tests)
tests/e2e/national-audit/
.github/workflows/ci.yml          # lint + contract + pytest
CHANGELOG.md
CONTRIBUTING.md
# package metadata ready to tag
```

## Next steps

1. `/to-spec` against this handoff → implement P5.  
2. Close [Accept P5 locked spec](https://github.com/apexshift/sageo/issues/24) when the handoff is accepted — **final Accept** on the master five-phase map.  
3. After implement + tag: external Skill contributions per CONTRIBUTING.

## Out of scope for P5 implement (on this handoff’s Plan-don’t-do boundary for the map; implement may do these)

Wayfinding map excluded implementing Actions YAML and cutting tags; **implement Spec** includes those as deliverables. Still out of product scope: live CI vendor calls; opening Agents/Orchestrator/Connectors to external contrib; auto-publish / write scopes.
