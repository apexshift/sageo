# Golden fixtures: evidence-packager

Hermetic Skill-package goldens (no live APIs). Fixture class: **evidence-bundle**.
`evidence_requirement: partial` — only packaging claims get Evidence; procedural
bundle assembly does not invent SEO/AIO/GEO metrics.

## Layout

```text
tests/skills/measurement-prioritisation/evidence-packager/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/bundle.json   # { findings[], evidence[], ranked_ids? }
    expected.json       # { package, findings, evidence }
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | findings + evidence + ranked_ids | `package.ready` pass; review-ready package |
| `empty-bundle` | empty findings/evidence | `package.ready` fail |
| `incomplete-evidence` | Evidence missing required fields | `package.incomplete` fail |
| `nhv-items` | upstream NHV Evidence present | `package.ready` pass + `package.nhv_pending` fail |

Packages upstream findings/Evidence into a review-ready bundle without inventing claims.
