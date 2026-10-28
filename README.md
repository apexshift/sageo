# SageO

A collection of agents and agent skills for repetitive, consistent search optimisation across local, national, and global reach — aligned to the SEO, AIO, and GEO pillars.

SageO helps SEO practitioners run the repetitive, labour-heavy optimisation work that has to stay consistent — across local, national, and global reach. It is a collection of Agents and Skills organised by capability pillar, framed around SEO, AIO, and GEO outcomes. Every claim carries Evidence; nothing publishes to a live site without a Human review gate.

Builders extend SageO by adding Skills under the five capability pillars and composing them into Agents — contracts first, then code where execution is required.

## Why SageO / pillars

**Capability pillars** organise Skills on disk: Technical Foundation, Content & Answer Quality, Authority & Trust, Measurement & Prioritisation, and Local / Geographic.

**Outcome pillars** frame what SageO optimises for: **SEO** (classic SERP), **AIO** (answer engines / AI overviews / LLM-cited answers), and **GEO** (generative engine optimisation). Catalogue and docs group by capability pillar first; outcome tags are filters, not folders.

**Reach** is the local, national, or global scope of a piece of work. Reach is not an Outcome pillar and is not the meaning of GEO.

Details live in [`docs/architecture.md`](docs/architecture.md).

## Architecture

System layers, Evidence / Decision logs, Human review gates, and the P1–P5 roadmap: [`docs/architecture.md`](docs/architecture.md).

## Quickstart

```bash
git clone https://github.com/apexshift/sageo.git
cd sageo
cp .env.example .env   # placeholders only; connectors land in P3
pip install -e ".[dev]"
make test
```

`make test` runs pytest (hermetic; no live API calls). The P1 template Skill is `skills/technical-foundation/schema-validator/`.

## Repository layout

```text
sageo/
├── AGENTS.md, GLOSSARY.md, README.md, LICENSE
├── docs/            # agents/, handoffs/, research/, templates/, governance prose
├── skills/          # capability-pillar library (source of truth)
├── agents/          # Agent contracts (placeholder in P1)
├── orchestrator/    # Orchestrator contract (placeholder in P1)
├── connectors/      # MCP server packs (placeholder in P1)
├── src/sageo/       # shared Python library
├── runs/            # local run artifacts (gitignored contents)
└── tests/
```

## Ethics & review gates

White-hat rules, Evidence requirements, Human review gates, and connector read-only policy through P5: [`docs/ethical-accountability-policy.md`](docs/ethical-accountability-policy.md).

## Contributing

External pull requests wait until the first public release after P5. Until then, open issues for discussion.

Contribution contract: [`CONTRIBUTING.md`](CONTRIBUTING.md). Short pointer:
[`docs/contribution-guidelines.md`](docs/contribution-guidelines.md).

## License

MIT. See [`LICENSE`](LICENSE).
