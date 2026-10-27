# Contribution guidelines

This is a **summary posture** for P1. A full `CONTRIBUTING.md` ships at first public release (P5). Until then, treat this document as the contribution contract.

## Not open for external PRs until first public release post-P5

External pull requests are accepted **after** P5’s locked spec is implemented and tagged as a first public release. The repository may be public earlier as **read-only / not ready for contrib**.

Maintainers implement the five-phase bootstrap (P1–P5) on the [master map](https://github.com/apexshift/sageo/issues/1). Outside that window, please open issues for discussion rather than PRs.

## Later: Skills + docs/fixes first

When the door opens after public release, outsiders may contribute:

- **Skills** under the correct capability pillar
- **Docs and fixes** (typos, clarifications, test goldens for existing Skills)

Agents, Orchestrator, and Connectors remain **maintainers-only** until a later policy revisits that scope.

## Skill contribution bar

A contributed Skill must:

- [ ] Ship a valid `SKILL.md` under the correct capability pillar path (`skills/<pillar-slug>/<skill-name>/`)
- [ ] Match directory name to frontmatter `name` and `metadata.capability_pillar` to the parent folder slug
- [ ] Declare `primary_outcome` (`SEO` | `AIO` | `GEO`) and required metadata (`version`, `evidence_requirement`, `human_review_gate`)
- [ ] Include required body sections: Purpose, Inputs, Outputs, Evidence, Human review, Procedure
- [ ] Obey the Evidence contract (no invented metrics; use `needs_human_verification` when sources fail or judgment is required)
- [ ] Stay white-hat (no scaled content abuse or manipulative tactics)
- [ ] Include hermetic golden tests (no live API calls in the suite), matching the master test-strategy Decision on [#12](https://github.com/apexshift/sageo/issues/12)
- [ ] Respect Human review gates (no auto-publish / live mutation without `human_review_gate: required` and Orchestrator enforcement)

Maintainers reject “guaranteed rankings” framing and any Skill that mutates live sites without a Human review gate. Copy the template at `docs/templates/SKILL.md`. See also `docs/ethical-accountability-policy.md` and `GLOSSARY.md`.

## Propose via issues first

Before writing a Skill or substantial docs change:

1. Open a GitHub issue describing the gap, pillar, and intended `primary_outcome`.
2. Wait for maintainer feedback on fit with the phase map and roster.
3. Implement only after the issue is labelled `ready-for-agent` (or equivalent maintainer go-ahead).

Small typo fixes may skip the proposal step after public release; still prefer issues when behaviour or contracts change.

## Code of conduct (stub)

Be respectful, assume good faith, and keep discussion about the work. Harassment, personal attacks, and bad-faith contributions are not welcome. A fuller Code of Conduct may land with the P5 public-release `CONTRIBUTING.md`; until then, maintainers may refuse or remove contributions that make collaboration unsafe.
