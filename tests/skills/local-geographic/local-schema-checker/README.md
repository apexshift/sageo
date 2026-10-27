# Golden fixtures: local-schema-checker

Hermetic Skill-package goldens (no live APIs). Fixture class: **page-html**.

## Layout

```text
tests/skills/local-geographic/local-schema-checker/
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
| `happy` | LocalBusiness with name, address, telephone | pass present + name + address + telephone |
| `missing-address` | LocalBusiness without address | fail address; other fields pass |
| `nap-conflict` | two LocalBusiness blocks, different names | pass primary fields + NHV nap_conflict |
| `malformed-jsonld` | invalid JSON in ld+json script | fail jsonld.parse |

Signals covered: LocalBusiness presence, name, PostalAddress (`streetAddress` + `addressLocality`), telephone, NAP conflicts, JSON-LD parse failures.
