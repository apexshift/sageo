# Example: AFK automation (pattern + hard limits)

“Away from keyboard” here means **scheduling or batching Agent/Orchestrator
Runs** so diagnose work proceeds without a human watching every Skill. It does
**not** mean unattended live-site changes.

## What can run without a human at the keyboard

| Work | AFK-friendly? | Why |
| --- | --- | --- |
| Skills with `human_review_gate: not_required` (e.g. many findings Skills) | Yes | Emit Evidence only |
| `technical-findings` Agent | Yes | Gate `not_required`; findings only |
| Orchestrator steps until a required gate | Yes | Runs until `awaiting_approval` |
| Stubbed / recorded-HTTP tests and `make ci` | Yes | Hermetic; no live vendors required |

## What must wait for a human

| Work | AFK-friendly? | Why |
| --- | --- | --- |
| Agents with `human_review_gate: required` (`content-aio`, `measurement-evidence`, `local-reach`) | **No past the gate** | Orchestrator owns the stop until Decision log approval |
| Any live-site publish or mutation | **Never unattended** | Ethics + Human review policy |
| Inventing metrics when Connectors fail | Forbidden | Use `needs_human_verification` |

SageO does not auto-publish remediations. AFK automation stops at the gate;
a practitioner resumes with recorded approval.

## Practical pattern (shipped primitives)

1. **Start a Run** via Orchestrator `run` / Agent `run_agent`, or the operator
   bridge / desktop New Run (`python -m sageo.operator start-thin-audit`) with
   Property refs + Reach (see [national audit](national-audit.md) and
   [operator desktop](operator-desktop.md)).
2. **Poll or wait** until `gate_state == awaiting_approval` (or status
   `awaiting_human_review`) — Progress watch in the desktop, or bridge
   `get-progress` / watch.
3. **Notify a human** (email, chat, ticket — your ops layer; not shipped as a
   SageO Connector). The desktop Review stage is the local interactive path.
4. **Resume** with `resume` / `resume_agent` / bridge `resume-run` and
   `approved=True` only after review (optional `operator_note`); rejection
   stops the Run without executing the gated continuation.
5. **Read** `runs/<id>/evidence.jsonl`, `decision_log.jsonl`, and
   `metrics.json` (Findings in the desktop browses Evidence).

### Sketch (illustration only)

```text
run → … Skills/Agents … → gate awaiting_approval
        ↑                                    |
   unattended OK                      human required
                                             ↓
                                    resume(approved=…)
                                             ↓
                                    metrics / package
```

Wire the notify/resume loop with your own scheduler (cron, CI workflow_dispatch,
queue worker). SageO ships the Run/gate primitives and hermetic tests — not a
hosted AFK SaaS.

## Hard limits (do not “automate away”)

- Do not set `approved=True` from a bot without a real human decision.
- Do not bypass Orchestrator gates to keep a cron job green.
- Do not store production Connector secrets in the repo; use env vars /
  [connector credentials](connector-credentials.md).
- Default CI stays secret-free and does not call live vendors.

## Roadmap

A future Spec may document a reference “notify on gate” helper or sample
scheduler. Until then, treat AFK as **ops around** `run` / `resume`, not a new
Agent that skips Human review.
