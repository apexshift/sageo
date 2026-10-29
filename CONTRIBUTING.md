# Contributing to SageO

Thanks for your interest in SageO. This document is the contribution contract
after the first public release
([`v0.1.0`](https://github.com/apexshift/sageo/releases/tag/v0.1.0)).

For ethics and positioning, also read:

- [`docs/ethical-accountability-policy.md`](docs/ethical-accountability-policy.md)
- [`README.md`](README.md)
- [`LICENSE`](LICENSE) (MIT)
- [`GLOSSARY.md`](GLOSSARY.md)

A shorter historical summary lives in
[`docs/contribution-guidelines.md`](docs/contribution-guidelines.md); **this
file wins** when they differ.

## Timing

**External pull requests are accepted** after the first public release tag
(`v0.1.0`). Prefer opening an issue before substantial Skill or docs work so
maintainers can confirm fit.

## How to propose work

Before writing a Skill or a substantial docs change:

1. Open a GitHub issue describing the gap, capability pillar, and intended
   `primary_outcome` (`SEO` | `AIO` | `GEO`).
2. Wait for maintainer feedback on fit with the roster and roadmap.
3. Implement only after the issue is labelled `ready-for-agent` (or an
   equivalent maintainer go-ahead).

Small typo fixes may skip the proposal step **after** the first public
release; still prefer issues when behaviour or contracts change.

## What outsiders may contribute

After the first public release tag, outsiders may contribute:

- **Skills** under the correct capability pillar
- **Docs and fixes** (typos, clarifications, test goldens for existing Skills)

**Agents, Orchestrator, Connectors, the operator bridge (`sageo.operator`), and
`apps/operator-desktop` remain maintainer-only** until a later policy revisits
that scope.

## Skill contribution bar

A contributed Skill must:

- [ ] Ship a valid `SKILL.md` under the correct capability pillar path
      (`skills/<pillar-slug>/<skill-name>/`)
- [ ] Match directory name to frontmatter `name` and
      `metadata.capability_pillar` to the parent folder slug
- [ ] Declare `primary_outcome` (`SEO` | `AIO` | `GEO`) and required metadata
      (`version`, `evidence_requirement`, `human_review_gate`)
- [ ] Include required body sections: Purpose, Inputs, Outputs, Evidence,
      Human review, Procedure
- [ ] Obey the **Evidence** contract (no invented metrics; use
      `needs_human_verification` / NHV when sources fail or judgment is
      required)
- [ ] Use glossary vocabulary correctly: **Evidence**, **Reach** (local /
      national / global scope), **GEO** (generative Outcome pillar — not
      geographic Reach)
- [ ] Stay **white-hat** (no scaled content abuse or manipulative tactics)
- [ ] Include hermetic golden tests (no live API calls in the default suite),
      matching the test-strategy Decision on
      [#12](https://github.com/apexshift/sageo/issues/12)
- [ ] Respect **Human review** gates (no auto-publish / live mutation without
      `human_review_gate: required` and Orchestrator enforcement)

Maintainers reject “guaranteed rankings” framing and any Skill that mutates
live sites without a Human review gate. Copy the template at
[`docs/templates/SKILL.md`](docs/templates/SKILL.md).

## License

Contributions are accepted under the MIT [`LICENSE`](LICENSE).

## Code of conduct (stub)

Be respectful, assume good faith, and keep discussion about the work.
Harassment, personal attacks, and bad-faith contributions are not welcome.
Maintainers may refuse or remove contributions that make collaboration unsafe.

## First public release

Before the first public tag, maintainers follow
[`docs/first-public-release-checklist.md`](docs/first-public-release-checklist.md).
