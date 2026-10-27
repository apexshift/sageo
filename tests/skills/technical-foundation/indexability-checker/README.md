# Golden fixtures: indexability-checker

Hermetic Skill-package goldens (no live APIs). Fixture class: **headers-html**.

## Layout

```text
tests/skills/technical-foundation/indexability-checker/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/response.json   # { status, headers }
    input/page.html
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | 200, no blocking robots | pass status + X-Robots-Tag + robots meta |
| `noindex-meta` | 200, meta `noindex` | fail robots meta; status/header pass |
| `signal-conflict` | header allows index, meta `noindex` | fail meta + conflict with `needs_human_verification` |

Signals covered: HTTP status, `X-Robots-Tag`, robots meta.
