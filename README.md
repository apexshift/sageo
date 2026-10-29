# SageO

A collection of agents and agent skills for repetitive, consistent search optimisation across local, national, and global reach — aligned to the SEO, AIO, and GEO pillars.

SageO helps SEO practitioners run the repetitive, labour-heavy optimisation work that has to stay consistent — across local, national, and global reach. It is a collection of Agents and Skills organised by capability pillar, framed around SEO, AIO, and GEO outcomes. Every claim carries Evidence; nothing publishes to a live site without a Human review gate.

Builders extend SageO by adding Skills under the five capability pillars and composing them into Agents — contracts first, then code where execution is required.

## Why SageO / pillars

**Capability pillars** organise Skills on disk: Technical Foundation, Content & Answer Quality, Authority & Trust, Measurement & Prioritisation, and Local / Geographic.

**Outcome pillars** frame what SageO optimises for: **SEO** (classic SERP), **AIO** (answer engines / AI overviews / LLM-cited answers), and **GEO** (generative engine optimisation). Catalogue and docs group by capability pillar first; outcome tags are filters, not folders.

**Reach** is the local, national, or global scope of a piece of work. Reach is not an Outcome pillar and is not the meaning of GEO.

Details live in [`docs/architecture.md`](docs/architecture.md).

## Documentation

| Doc | Description |
| --- | --- |
| [`docs/architecture.md`](docs/architecture.md) | Layers, pillars, Evidence / Decision logs, Human review gates, phase status |
| [`GLOSSARY.md`](GLOSSARY.md) | Domain vocabulary (Skill, Agent, Orchestrator, Evidence, Property refs, Reach, GEO, …) |
| [`docs/examples/`](docs/examples/) | Honest walkthroughs (national/local audits, onboarding, operator desktop, AFK limits, …) |
| [`apps/operator-desktop/README.md`](apps/operator-desktop/README.md) | Electron operator shell over a local checkout (wizard → Progress → Findings → Review) |
| [`docs/ethical-accountability-policy.md`](docs/ethical-accountability-policy.md) | White-hat rules, Evidence, gates, read-only Connectors |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | External PRs after `v0.1.0`, Skill contribution bar, maintainer-only surfaces |
| [`docs/first-public-release-checklist.md`](docs/first-public-release-checklist.md) | Maintainer gate before the first public tag |
| [`CHANGELOG.md`](CHANGELOG.md) | Product release notes (Keep a Changelog) |
| [`docs/templates/`](docs/templates/) | Copy-ready `SKILL.md` / `AGENT.md` contracts |
| [`docs/handoffs/`](docs/handoffs/) | Locked phase-spec handoffs (P1–P5) |
| [`LICENSE`](LICENSE) | MIT |

## Quickstart

```bash
git clone https://github.com/apexshift/sageo.git
cd sageo
cp .env.example .env   # placeholders only; never commit real secrets
pip install -e ".[dev]"
make ci                # lint + contract lint + pytest (hermetic)
```

`make ci` is the hermetic default (no live vendor calls; no production secrets).
For pytest alone: `make test`. Walkthroughs: [`docs/examples/`](docs/examples/).
A good first Skill to read: [`skills/technical-foundation/schema-validator/`](skills/technical-foundation/schema-validator/).

Optional local operator UI (after install): see
[`apps/operator-desktop/README.md`](apps/operator-desktop/README.md) and
[`docs/examples/operator-desktop.md`](docs/examples/operator-desktop.md).

## Repository layout

```text
sageo/
├── AGENTS.md, GLOSSARY.md, README.md, LICENSE, CONTRIBUTING.md, CHANGELOG.md
├── docs/            # architecture, ethics, examples/, templates/, handoffs/, …
├── skills/          # 14 Skills under five capability pillars
├── agents/          # technical-findings, content-aio, measurement-evidence, local-reach
├── orchestrator/    # Orchestrator contract + thin_audit routing
├── connectors/      # read-only MCP packs: gsc, ga4, crawl-serp
├── src/sageo/       # shared Python library (operator bridge, lint, runtimes, metrics, …)
├── apps/            # operator-desktop Electron shell (wizard → Progress → Findings → Review)
├── runs/            # local run artifacts (gitignored contents)
└── tests/           # goldens, e2e/national-audit, contract lint, …
```

## Ethics & review gates

White-hat rules, Evidence requirements, Human review gates, and connector
read-only policy through P5:
[`docs/ethical-accountability-policy.md`](docs/ethical-accountability-policy.md).

## Contributing

External pull requests follow [`CONTRIBUTING.md`](CONTRIBUTING.md) after the
first public release tag ([`v0.1.0`](https://github.com/apexshift/sageo/releases/tag/v0.1.0)).

Contribution contract: [`CONTRIBUTING.md`](CONTRIBUTING.md). Short pointer:
[`docs/contribution-guidelines.md`](docs/contribution-guidelines.md).

## License

MIT. See [`LICENSE`](LICENSE).
