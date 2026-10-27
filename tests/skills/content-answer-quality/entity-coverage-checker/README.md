# Golden fixtures: entity-coverage-checker

Hermetic Skill-package goldens (no live APIs / LLMs). Fixture class: **page-html**.

## Layout

```text
tests/skills/content-answer-quality/entity-coverage-checker/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/page.html
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | Organization + sameAs + visible name | pass schema + sameAs + visible |
| `thin-coverage` | Organization without sameAs; name absent from body | fail sameAs + visible |
| `name-conflict` | two Organizations, different names | pass primary signals + NHV name_conflict |

Signals: named schema entity, `sameAs`, visible name mention, name conflicts.
