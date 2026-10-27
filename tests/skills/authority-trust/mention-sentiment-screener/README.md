# Golden fixtures: mention-sentiment-screener

Hermetic Skill-package goldens (no live APIs). Fixture class: **opportunity-corpus**.

## Layout

```text
tests/skills/authority-trust/mention-sentiment-screener/
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
| `happy` | brand mention, positive/neutral, no risk | pass sentiment_ok + low_risk |
| `thin-corpus` | no brand mentions | fail sentiment_ok |
| `signal-conflict` | mixed sentiment or safe+risk cues | fail sentiment_ok + NHV signal_conflict |
| `negative-risk` | negative sentiment and/or risk signals | fail sentiment_ok + risk_detected |

White-hat only: screens mentions for sentiment/risk; does not propose outreach or suppression.
