# Golden fixtures: crawl-issue-extractor

Hermetic Skill-package goldens (no live APIs). Fixture class: **crawl-log**.
The Skill declares `connectors: crawl_serp`; goldens pass the log directly.
Unit tests mock the connector fetch path.

## Layout

```text
tests/skills/technical-foundation/crawl-issue-extractor/
  evidence.schema.json
  README.md
  test_golden.py
  unit/test_extract_with_connector.py
  fixtures/<case>/
    input/crawl_log.json   # { entries: [{url, status, redirect_count, error}] }
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | all 200, no redirects/errors | pass client/server/redirect/timeout |
| `http-errors` | 404, 503, long redirect, timeout | fail those categories |
| `soft-404` | status 200 with `soft_404` error | fail `crawl.soft_404` (NHV) |

Extracts and classifies crawl issues from a crawl-log snapshot (or via a mocked
`crawl_serp` connector).
