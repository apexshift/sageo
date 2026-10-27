# Golden fixtures: citation-opportunity-identifier

Hermetic Skill-package goldens (no live APIs). Fixture class: **opportunity-corpus**.

## Layout

```text
tests/skills/authority-trust/citation-opportunity-identifier/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/corpus.json   # { brand, candidates[] }
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | brand-mention candidate, unpaid, no spam | pass opportunity + white_hat |
| `thin-corpus` | paid/spam-only candidate | fail opportunity_found |
| `signal-conflict` | brand mention + paid_placement | fail opportunity + NHV signal_conflict |

White-hat only: no link-buying or spam-network recommendations.
