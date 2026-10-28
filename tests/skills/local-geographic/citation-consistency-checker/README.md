# Golden fixtures: citation-consistency-checker

Hermetic Skill-package goldens (no live APIs). Fixture class: **listings-nap**.

## Layout

```text
tests/skills/local-geographic/citation-consistency-checker/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/listings.json   # { canonical, listings[] }
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | listings match canonical NAP | pass nap_consistent |
| `thin-listings` | empty listings array | fail nap_consistent |
| `nap-mismatch` | listing phone/address differs | fail nap_consistent + nap_mismatch |
| `nap-conflict` | near-variant name (substring) | fail nap_consistent + NHV nap_conflict |
| `incomplete-listing` | listing missing telephone | fail nap_consistent + listing_incomplete |

Compares directory listings to a canonical NAP (name, streetAddress, addressLocality, telephone).
