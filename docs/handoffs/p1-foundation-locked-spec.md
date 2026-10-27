# P1 Foundation & governance — locked spec handoff

**Status:** Locked for `/to-spec` → implement  
**Phase map:** [Phase map: P1 Foundation & governance](https://github.com/apexshift/sageo/issues/25)  
**Master map:** [Master map: SageO five-phase bootstrap](https://github.com/apexshift/sageo/issues/1)  
**Accept on master:** [Accept P1 locked spec](https://github.com/apexshift/sageo/issues/16)

This handoff is the single linked artifact required by [Define phase exit criteria for locked specs](https://github.com/apexshift/sageo/issues/13). It does **not** implement P1 files; it specifies what implement must produce.

## Inherit from master

Implement must obey all master Decisions so far on [#1](https://github.com/apexshift/sageo/issues/1), including: hybrid layout; Skill / Agent / Orchestrator contracts; Evidence & Decision logs (`runs/<id>/`); connector policy (MCP, read-only through P5); test strategy ramp; ethics; positioning copy; MIT is set on the P1 map.

Domain language: root `GLOSSARY.md`.

## Exit criteria checklist

| Criterion | Satisfied by |
| --- | --- |
| Repo tree per hybrid layout | Master [Freeze hybrid Markdown+Python layout](https://github.com/apexshift/sageo/issues/8) |
| Governance docs (architecture, ethical-accountability, contribution posture summary, skill/agent templates) | [Outline P1 governance documents](https://github.com/apexshift/sageo/issues/27) |
| README with locked positioning | [Outline README structure for P1](https://github.com/apexshift/sageo/issues/30) + [Write SageO positioning copy](https://github.com/apexshift/sageo/issues/3) |
| Test harness + contract linter + one template Skill golden | [Freeze P1 test harness stack](https://github.com/apexshift/sageo/issues/29) + [Pick the P1 template Skill identity](https://github.com/apexshift/sageo/issues/28) |
| `.env.example` | [Freeze .env.example key list for P1](https://github.com/apexshift/sageo/issues/31) |
| `runs/` placeholder | Master layout + Evidence/logging ([#5](https://github.com/apexshift/sageo/issues/5), [#8](https://github.com/apexshift/sageo/issues/8)) |
| LICENSE | [Choose P1 repository license](https://github.com/apexshift/sageo/issues/26) — MIT |

## P1 decisions (detail lives on tickets)

1. **License — MIT** — root `LICENSE` + README license blurb. ([#26](https://github.com/apexshift/sageo/issues/26))
2. **Governance paths & outlines** ([#27](https://github.com/apexshift/sageo/issues/27))
   - `docs/architecture.md` — pointer + short system sketch (7 sections)
   - `docs/ethical-accountability-policy.md` — 7 sections (prose at implement)
   - `docs/contribution-guidelines.md` — summary posture (not full CONTRIBUTING.md)
   - `docs/templates/SKILL.md`, `docs/templates/AGENT.md`
3. **Template Skill** — `skills/technical-foundation/schema-validator/`  
   `primary_outcome: SEO`, `evidence_requirement: full`, `human_review_gate: not_required`  
   Purpose: validate schema/structured data on a page fixture → Evidence. ([#28](https://github.com/apexshift/sageo/issues/28))
4. **Test harness** — pytest + `pyproject.toml`; contract lint module under `src/sageo/` exercised by pytest; golden at `tests/skills/technical-foundation/schema-validator/`; `make test`; **no CI until P5**. ([#29](https://github.com/apexshift/sageo/issues/29))
5. **README** — 10 sections: title+one-liner → practitioner paragraph → builders line → pillars → architecture → quickstart → layout → ethics → contributing → MIT. ([#30](https://github.com/apexshift/sageo/issues/30))
6. **`.env.example` keys** (empty placeholders):  
   `GSC_CLIENT_EMAIL`, `GSC_PRIVATE_KEY`, `GSC_PROPERTY_URL`,  
   `GA4_PROPERTY_ID`, `GA4_CREDENTIALS_JSON`,  
   `CRAWL_SERP_API_KEY`, `CRAWL_SERP_BASE_URL`  
   Comments: P3 connectors; read-only through P5. ([#31](https://github.com/apexshift/sageo/issues/31))

## Deliverables implement must create

```text
LICENSE
README.md
.gitignore          # include .env, runs/* (keep runs/.gitkeep or runs/README.md)
.env.example
Makefile            # test → pytest
pyproject.toml
GLOSSARY.md         # already seeded; keep aligned
AGENTS.md
docs/architecture.md
docs/ethical-accountability-policy.md
docs/contribution-guidelines.md
docs/templates/SKILL.md
docs/templates/AGENT.md
docs/agents/        # already present from setup
skills/technical-foundation/schema-validator/SKILL.md
tests/skills/technical-foundation/schema-validator/
src/sageo/          # contract lint module + package
runs/.gitkeep
agents/             # placeholder dir OK in P1
orchestrator/       # placeholder dir OK in P1
connectors/         # placeholder dir OK in P1
```

## Next steps

1. `/to-spec` against this handoff (and phase map #25) → implementation tickets.  
2. Implement P1 (post-map skills: test-protocol, living-docs, merge-ready).  
3. Close [Accept P1 locked spec](https://github.com/apexshift/sageo/issues/16) on the master map when the handoff is accepted (spec locked; implement may follow).  
4. Then [Chart phase map P2](https://github.com/apexshift/sageo/issues/17).

## Out of scope for P1 implement

- Full Skills library (P2)
- Live connectors / Orchestrator (P3)
- Reference Agents (P4)
- CI, packaging, public-release CONTRIBUTING.md (P5)
- Auto-publish or write scopes
