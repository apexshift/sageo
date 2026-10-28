# Example: local Reach workflow

When **Reach = local**, the Orchestrator includes the shipped
[`agents/local-reach/`](../../agents/local-reach/) Agent (GBP → LocalBusiness
schema → NAP consistency). When Reach ≠ local, that Agent is omitted.

This walkthrough uses the real Agent contract and hermetic golden at
[`tests/agents/local-reach/`](../../tests/agents/local-reach/).

## What runs

| Step | Layer | Identity |
| --- | --- | --- |
| Schedule | Orchestrator | Include `local-reach` only when `request.reach` is `local` |
| Agent | `local-reach` | [`agents/local-reach/AGENT.md`](../../agents/local-reach/AGENT.md) |

Typical full local audit still sequences technical → content/AIO → measurement
(same as [national audit](national-audit.md)), **plus** `local-reach` when
Reach is local. `local-reach` does not replace the national path; it adds
Local / Geographic Skills.

## Skill order (happy path)

1. `gbp-profile-auditor`
2. `local-schema-checker`
3. `citation-consistency-checker`

## Human review gate

`human_review_gate: required`. Pause after Skills complete and **before** any
GBP/listing change recommendations are finalised. Orchestrator owns the stop;
approval is recorded in the Decision log.

## Try the hermetic Agent golden

```bash
pip install -e ".[dev]"
pytest tests/agents/local-reach/test_golden.py
```

Skills are stubbed; no live GBP or vendor calls in the default suite.
