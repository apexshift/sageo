# Golden fixtures: schema-validator

Hermetic Skill-package goldens (no live APIs). P2 reference layout for Core Skills.

## Layout

```text
tests/skills/technical-foundation/schema-validator/
  evidence.schema.json          # Evidence shape (evidence_requirement: full)
  README.md
  test_golden.py
  fixtures/<case>/
    input/page.html             # page-html fixture class
    expected.json               # findings + evidence
```

Multi-case Skills keep per-case `fixtures/<case>/{input/,expected.json}` and a single Skill-level `evidence.schema.json`. Shared asserts live in `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | Valid Organization JSON-LD | pass finding + high-confidence Evidence |
| `malformed-jsonld` | Invalid JSON in `ld+json` script | fail finding + high-confidence Evidence |
| `contradictory-types` | Two Organization blocks, different names | pass per block + Evidence with `confidence: needs_human_verification` for contradiction |
