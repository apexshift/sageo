# Examples

Honest walkthroughs of the **shipped** SageO tree, plus clear **pattern /
roadmap** notes where a playbook is not packaged yet. These are not product
demos that invent Agents or promise rankings — they point at real Skills,
Agents, Orchestrator contracts, Connectors, and hermetic tests.

## Shipped walkthroughs

| Example | What it shows |
| --- | --- |
| [National audit](national-audit.md) | Orchestrator → three Agents, Measurement Human review gate, Evidence / Decision logs, metrics on a Run |
| [Local Reach workflow](local-workflow.md) | `local-reach` Agent (GBP → schema → NAP) when Reach = local; required gate before listing changes |
| [Technical audit and onboarding](technical-audit-and-onboarding.md) | Practitioner onboarding path + `technical-findings` as the technical-audit entry point |
| [Skill package layout](skill-layout.md) | Anatomy of a real Skill on disk (`schema-validator`) |
| [Connector credentials](connector-credentials.md) | Configuring GSC / GA4 / crawl-serp via `.env.example` (placeholders only) |

## Patterns (partially shipped)

| Example | What it shows |
| --- | --- |
| [Global Reach workflow](global-workflow.md) | Reach = global on the thin-audit Agents; no separate global Agent; `local-reach` omitted |
| [AFK automation](afk-automation.md) | What can run unattended vs hard stops at Human review gates; ops around `run` / `resume` |

Related living docs: [`docs/architecture.md`](../architecture.md),
[`GLOSSARY.md`](../../GLOSSARY.md),
[`docs/ethical-accountability-policy.md`](../ethical-accountability-policy.md).
