# Example: national audit

Walk through the shipped **national** Reach audit path: Orchestrator schedules
three Agents, Measurement pauses for a Human review gate, Evidence and Decision
logs land under a Run directory, and the metrics helper reports cost + Evidence
completeness.

This mirrors the hermetic golden at
[`tests/e2e/national-audit/`](../../tests/e2e/national-audit/).

## What runs

| Step | Layer | Identity |
| --- | --- | --- |
| 1 | Orchestrator | [`orchestrator/ORCHESTRATOR.md`](../../orchestrator/ORCHESTRATOR.md) (`thin_audit` playbook) |
| 2 | Agent | [`agents/technical-findings/`](../../agents/technical-findings/) |
| 3 | Agent | [`agents/content-aio/`](../../agents/content-aio/) |
| 4 | Agent (gated) | [`agents/measurement-evidence/`](../../agents/measurement-evidence/) |

Agents compose Skills; they never call other Agents. The Orchestrator owns
sequencing and the system stop at required Human review gates.

## Skill order (happy path)

From each Agent’s contract and the e2e expected fixture:

1. **technical-findings** — `crawl-issue-extractor`, `indexability-checker`,
   `schema-validator`, `cwv-scorer`
2. **content-aio** — `intent-classifier`, `answer-extractability-scorer`,
   `entity-coverage-checker`, `citation-opportunity-identifier`
3. **measurement-evidence** — `mention-sentiment-screener`,
   `severity-impact-scorer`, `evidence-packager`

## Property refs

Start the Run with Orchestrator **Property refs**: required `site_url`,
optional `gsc_property` and `ga4_property` (empty optionals omitted). The
operator desktop New Run form and `sageo.operator start-thin-audit` collect the
same mapping.

## Human review gate

`measurement-evidence` declares `human_review_gate: required`. After its Skills
run (including `evidence-packager`), the Human review gate pauses until a
human approves in the Decision log. The Orchestrator surfaces that pause
end-to-end; approval resumes the Run (CLI/`resume`, bridge `resume-run`, or
the desktop [Review](operator-desktop.md) stage).

Nothing publishes to or mutates a live site without that gate and recorded
approval. Findings are Evidence-backed diagnostics for a practitioner — SageO
does not auto-publish remediations.

## Run artifacts

Under `runs/<id>/` (gitignored contents; created at runtime):

- `evidence.jsonl` — Evidence rows (`claim`, `source`, `observed_at`,
  `confidence`; rows with `needs_human_verification` need
  `verification_reason`)
- `decision_log.jsonl` — Orchestrator and Agent decisions, including gate
  awaiting / approved entries
- `metrics.json` — from `sageo.metrics.write_run_metrics` (cost class estimates
  + Evidence completeness). No invented ranking or traffic KPIs.

Nested Agent runs in the e2e live under `runs/<id>/agents/<agent-name>/`.

## Try the hermetic e2e

```bash
pip install -e ".[dev]"
pytest tests/e2e/national-audit/test_e2e.py
# or the full hermetic suite:
make ci
```

Default CI and pytest stay secret-free: Skills are stubbed and Connectors are
not called live in this golden.
