# Golden fixtures: severity-impact-scorer

Hermetic Skill-package goldens (no live APIs). Fixture class: **issue-list**.

## Layout

```text
tests/skills/measurement-prioritisation/severity-impact-scorer/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/issues.json   # { issues: [{id, summary?, severity, impact}], alternate_issues? }
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | valid severity×impact on each issue | pass scored + rank; Evidence per issue |
| `thin-issues` | empty issues array | fail scored |
| `incomplete-scores` | missing/invalid severity or impact | fail scored + incomplete |
| `score-conflict` | alternate_issues disagree on score | fail score_conflict (NHV) |

Scores each issue as `severity × impact` (integer 1–5 each) and ranks highest first.
