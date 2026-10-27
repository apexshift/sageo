# Golden fixtures: cwv-scorer

Hermetic Skill-package goldens (no live APIs). Fixture class: **lab-metrics**.

## Layout

```text
tests/skills/technical-foundation/cwv-scorer/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/metrics.json   # { lcp_ms, inp_ms, cls [, alternate] }
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | LCP/INP/CLS within good bars | pass all three metrics |
| `failing-lcp` | LCP 4200ms, INP/CLS good | fail LCP; pass INP + CLS |
| `metric-conflict` | primary good LCP, alternate failing LCP | pass primary scores + NHV conflict |

Thresholds (lab good): LCP ≤ 2500ms, INP ≤ 200ms, CLS ≤ 0.1.
