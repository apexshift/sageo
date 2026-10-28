# Example: technical audit and onboarding

Practitioners often start with a **technical diagnosis** before content or
local work. The shipped entry point is
[`agents/technical-findings/`](../../agents/technical-findings/) — crawl,
indexability, schema, and CWV blockers as one workflow.

## Onboarding path (honest)

| Step | What to do | Shipped pointer |
| --- | --- | --- |
| 1 | Skim glossary + architecture | [`GLOSSARY.md`](../../GLOSSARY.md), [`docs/architecture.md`](../architecture.md) |
| 2 | Install and run hermetic CI | `pip install -e ".[dev]"` then `make ci` |
| 3 | Read a Skill contract | [Skill layout](skill-layout.md) (`schema-validator`) |
| 4 | Run a technical Agent golden | `pytest tests/agents/technical-findings/test_golden.py` |
| 5 | See a full audit with gate + metrics | [National audit](national-audit.md) e2e |
| 6 | Configure Connectors only if needed | [Connector credentials](connector-credentials.md) |

There is no separate `onboarding` Agent. Onboarding is this practitioner path
over the shipped tree.

## Technical audit (Agent)

| Field | Value |
| --- | --- |
| Agent | `technical-findings` |
| Skills (order) | `crawl-issue-extractor` → `indexability-checker` → `schema-validator` → `cwv-scorer` |
| Human review gate | `not_required` (findings only; Measurement owns the package gate) |
| Cost model | `tokens_and_connector_calls` |

Skip `cwv-scorer` when lab metrics are absent (Agent contract condition).

### Try it

```bash
pytest tests/agents/technical-findings/test_golden.py
```

### Where it sits in a full audit

Orchestrator `thin_audit` still continues to `content-aio` and
`measurement-evidence` after technical findings. A “technical-only” session is
running this Agent (or stopping after its step) — not a different product
surface.

## Related audits

- Full national path: [national-audit.md](national-audit.md)
- Local GBP/schema/NAP: [local-workflow.md](local-workflow.md)
- Content / AIO Agent: [`agents/content-aio/`](../../agents/content-aio/)
