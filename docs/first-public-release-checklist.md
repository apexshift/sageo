# First public release checklist

Gate for cutting the first public product tag (expected `v0.1.0`) and GitHub
Release. Maintainers complete every item before tagging. External Skill
contributions follow [`CONTRIBUTING.md`](../CONTRIBUTING.md) only after this
tag exists.

## Before tag

- [ ] **CI green:** lint + contract lint + pytest (including
      `tests/e2e/national-audit/` as present)
- [ ] **Metrics on e2e:** metrics helper checks pass on the national-audit e2e
      Run (cost + Evidence completeness; no invented ranking/traffic KPIs)
- [ ] **CHANGELOG:** `CHANGELOG.md` has an entry for the product version being
      tagged (move Unreleased notes into a dated `## [0.1.0]` section as
      appropriate)
- [ ] **Versions:** product version in `pyproject.toml` matches the tag;
      every shipped Skill / Agent / Orchestrator has a valid semver
      `metadata.version` (independent — no lockstep with the product tag)
- [ ] **Docs published:** README, ethical accountability policy, and
      `CONTRIBUTING.md` are present and current
- [ ] **MIT LICENSE** present; **no secrets** in the tree (credentials via
      env / `.env.example` placeholders only)
- [ ] **Positioning / no-hype review:** README and release notes stay
      practitioner-first; no guaranteed rankings, autonomous publishing, or
      set-and-forget live-site claims
- [ ] **Cut release:** GitHub Release + package version tag published; release
      notes point at CHANGELOG and included component versions (or “see tree”)
