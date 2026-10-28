# First public release checklist

Gate for cutting the first public product tag (`v0.1.0`) and GitHub Release.
Maintainers complete every item before tagging. External Skill contributions
follow [`CONTRIBUTING.md`](../CONTRIBUTING.md) only after this tag exists.

## Before tag

- [x] **CI green:** lint + contract lint + pytest (including
      `tests/e2e/national-audit/` as present) — verified via `make ci`
- [x] **Metrics on e2e:** metrics helper checks pass on the national-audit e2e
      Run (cost + Evidence completeness; no invented ranking/traffic KPIs)
- [x] **CHANGELOG:** `CHANGELOG.md` has `## [0.1.0] - 2026-10-28` for the
      product version being tagged
- [x] **Versions:** product version in `pyproject.toml` is `0.1.0` (matches
      tag `v0.1.0`); every shipped Skill / Agent / Orchestrator has a valid
      semver `metadata.version` (independent — no lockstep with the product tag)
- [x] **Docs published:** README, ethical accountability policy, and
      `CONTRIBUTING.md` are present and current
- [x] **MIT LICENSE** present; **no secrets** in the tree (credentials via
      env / `.env.example` placeholders only)
- [x] **Positioning / no-hype review:** README and release notes stay
      practitioner-first; no guaranteed rankings, autonomous publishing, or
      set-and-forget live-site claims (hype language appears only as rejected
      framing in ethics/CONTRIBUTING)
- [ ] **Cut release:** GitHub Release + package version tag `v0.1.0` published
      after this prep merges to `main`; release notes point at CHANGELOG and
      included component versions (or “see tree”)
