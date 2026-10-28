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

### Added

- Shared metrics helper (`sageo.metrics`) for Run cost estimates and Evidence
  completeness.
- National-audit hermetic end-to-end golden under `tests/e2e/national-audit/`.
- Hermetic GitHub Actions CI (`make ci`: ruff lint, contract lint, pytest).
- Product CHANGELOG and version-sync posture for the first public release
  (expected product tag `v0.1.0`; included component versions: see tree
  `metadata.version`, typically starting at `0.1.0`).
