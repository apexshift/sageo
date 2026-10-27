# Golden fixtures: intent-classifier

Hermetic Skill-package goldens (no live APIs / LLMs). Fixture class: **query-page**.

## Layout

```text
tests/skills/content-answer-quality/intent-classifier/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/query.json   # { "query": "..." }
    input/page.html
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | informational query + how-to page | pass query/page/match |
| `mismatch` | transactional query + how-to page | pass query/page; fail match |
| `ambiguous-query` | "how to buy …" query | fail query + NHV ambiguous; page may still classify |

Classes: informational, transactional, navigational.
