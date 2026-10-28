# Changelog

All notable changes to the **SageO product** (installable package + GitHub
Release tag) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version layers

SageO uses two independent version layers:

1. **Product version** — `pyproject.toml` / GitHub Release tag (this CHANGELOG).
2. **Component semver** — each Skill, Agent, and Orchestrator
   `metadata.version`. Component versions are **independent**: they need not
   equal each other or the product tag (no lockstep).

Contract lint fails shipped packs that lack a valid semver `metadata.version`.

## [Unreleased]

Work landed on `main` toward the first public product tag (`v0.1.0`). Included
component versions: see tree `metadata.version` (typically starting at
`0.1.0`).

### Added

#### P5 — Quality, metrics & packaging (in progress)

- Shared metrics helper (`sageo.metrics`) for Run cost estimates and Evidence
  completeness.
- National-audit hermetic end-to-end golden under `tests/e2e/national-audit/`.
- Hermetic GitHub Actions CI (`make ci`: ruff lint, contract lint, pytest).
- Product CHANGELOG and version-sync posture (this file; contract lint rejects
  non-semver `metadata.version`).
- Public-release `CONTRIBUTING.md` and
  `docs/first-public-release-checklist.md`.

#### P4 — Workflow Agents

- Agent workflow black-box harness (`run_agent` / `resume_agent` with stubbed
  Skills).
- Four Agents with hermetic goldens: `technical-findings`, `content-aio`,
  `measurement-evidence`, and `local-reach`.

#### P3 — Data connections & Orchestrator

- Shared Connector helpers: NHV Evidence mapping and recorded-HTTP test
  fixtures (no live vendor calls in default tests).
- Read-only Connector packs: GSC, GA4, and crawl-serp.
- Orchestrator runtime: routing, prioritisation, sequential thin-audit
  scheduling, Human review gate stop/resume, shared Run directory with
  Evidence and Decision logs.

#### P2 — Core Skill library

- Fourteen Skills across the five capability pillars, each with hermetic
  goldens and Evidence contracts:
  - **Technical Foundation:** `schema-validator`, `indexability-checker`,
    `cwv-scorer`, `crawl-issue-extractor`
  - **Content & Answer Quality:** `intent-classifier`,
    `answer-extractability-scorer`, `entity-coverage-checker`
  - **Authority & Trust:** `citation-opportunity-identifier`,
    `mention-sentiment-screener`
  - **Local / Geographic:** `local-schema-checker`,
    `citation-consistency-checker`, `gbp-profile-auditor`
  - **Measurement & Prioritisation:** `severity-impact-scorer`,
    `evidence-packager`

#### P1 — Foundation & governance

- Hybrid Markdown + Python repository scaffold, installable `sageo` package,
  pytest harness, MIT license, and hermetic `make test`.
- Domain glossary, architecture docs, ethical accountability policy, and
  Skill/Agent templates.
- Skill package contract lint and the `schema-validator` golden Skill.
- README with locked positioning and quickstart.
