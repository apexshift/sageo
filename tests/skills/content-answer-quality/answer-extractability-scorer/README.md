# Golden fixtures: answer-extractability-scorer

Hermetic Skill-package goldens (no live APIs / LLMs). Fixture class: **page-html**.

## Layout

```text
tests/skills/content-answer-quality/answer-extractability-scorer/
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
| `happy` | single H1, short lead, ordered list | pass h1 + lead + structure |
| `weak-structure` | single H1, short lead, no list/Q&A | fail structure |
| `multiple-h1` | two H1s + lead + list | fail h1 + NHV signal_conflict; lead/structure pass |

Signals: H1 uniqueness, answer-first lead (≤40 words), list / definition list / question H2 structure.
