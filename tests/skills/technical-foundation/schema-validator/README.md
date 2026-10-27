# Golden fixtures: schema-validator

Hermetic Skill-package goldens (no live APIs).

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | Valid Organization JSON-LD | pass finding + high-confidence Evidence |
| `malformed-jsonld` | Invalid JSON in `ld+json` script | fail finding + high-confidence Evidence |
| `contradictory-types` | Two Organization blocks, different names | pass per block + NHV Evidence for contradiction |

Layout foreshadows the P2 golden strategy: `fixtures/<case>/input/` + `expected.json`.
