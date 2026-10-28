# Example: global Reach workflow (pattern)

**Reach = global** uses the same Outcome pillars (SEO / AIO / GEO) and the same
shipped Agents as a national audit. There is **no** separate “global-only”
Agent in the P4 roster — global is a Reach scope, not a GEO Outcome and not a
capability pillar.

## What is shipped today

| Piece | Status |
| --- | --- |
| Reach value `global` on Orchestrator `RunRequest` | Supported (Agents with a `reach` filter are omitted when they do not match) |
| `local-reach` Agent | Omitted when Reach ≠ `local` |
| `thin_audit` sequence | technical-findings → content-aio → measurement-evidence |
| Dedicated global e2e golden | **Not packaged yet** — follow [national audit](national-audit.md) + set Reach=`global` |

## Practitioner pattern

1. Set Orchestrator intent/playbook as for a thin audit; set **Reach = global**.
2. Expect the same three-Agent diagnose path as [national audit](national-audit.md).
3. Do **not** schedule `local-reach` (GBP/NAP) unless you also have local
   properties — Orchestrator omits it when Reach is global.
4. Keep Measurement’s Human review gate before any remediation pack is final.

GEO in SageO means **generative engine optimisation** (Outcome pillar), not
“geographic / global.” Global Reach can still use AIO/GEO outcome Skills via
`content-aio` and related Skills.

## Roadmap (not invented packs)

A future playbook may document global-specific property sets, language/locale
fixtures, or Connector scopes. Until then, treat global as Reach scoping on the
shipped thin-audit Agents — do not invent a `global-reach` Agent name in docs
or PRs without a Spec.
