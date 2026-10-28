# Example: Skill package layout

Every Skill is a directory under a capability pillar with a required
`SKILL.md` contract. Optional conventional subdirs: `scripts/`, `references/`,
`assets/`.

## Real pack: schema-validator

Path:
[`skills/technical-foundation/schema-validator/`](../../skills/technical-foundation/schema-validator/)

```text
skills/technical-foundation/schema-validator/
├── SKILL.md          # contract (frontmatter + body sections)
└── scripts/          # optional Python helpers for this Skill only
```

Frontmatter `name` must match the directory name; `metadata.capability_pillar`
must match the parent folder slug (`technical-foundation`). Required metadata
includes `version`, `primary_outcome`, `evidence_requirement`, and
`human_review_gate`.

Body sections required by contract lint: Purpose, Inputs, Outputs, Evidence,
Human review, Procedure.

## Templates and tests

- Copy-ready template: [`docs/templates/SKILL.md`](../templates/SKILL.md)
- Contribution bar: [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- Hermetic golden for this Skill:
  [`tests/skills/technical-foundation/schema-validator/`](../../tests/skills/technical-foundation/schema-validator/)

Shared helpers used by more than one Skill live under `src/sageo/`; Skill-local
code stays in that Skill’s `scripts/`.
