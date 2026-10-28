# Golden fixtures: gbp-profile-auditor

Hermetic Skill-package goldens (no live APIs). Fixture class: **gbp-fixture**.

## Layout

```text
tests/skills/local-geographic/gbp-profile-auditor/
  evidence.schema.json
  README.md
  test_golden.py
  fixtures/<case>/
    input/profile.json   # GBP profile snapshot (+ optional alternate)
    expected.json
```

Shared asserts: `sageo.testing.golden`.

## Cases

| Case | Input | Expectation |
| --- | --- | --- |
| `happy` | complete GBP profile | all completeness/quality findings pass |
| `incomplete-profile` | missing website/hours/description; low photos | fail those fields |
| `profile-conflict` | alternate disagrees on name/telephone | fail `gbp.profile_conflict` (NHV) |

Audits Google Business Profile completeness and quality signals from a fixture
snapshot (name, address, telephone, website, category, hours, description,
photos).
