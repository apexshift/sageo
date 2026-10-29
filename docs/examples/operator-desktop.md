# Example: operator desktop (local shell)

Run the shipped **Electron operator** over a local SageO checkout and Python
interpreter. The UI talks only to `python -m sageo.operator` (the operator
bridge) — no parallel approval store, no invented Evidence table.

Develop notes: [`apps/operator-desktop/README.md`](../../apps/operator-desktop/README.md).

## What you need

1. A SageO checkout with `pip install -e ".[dev]"` (or equivalent) in the
   interpreter you will select.
2. Node for the Electron shell (`cd apps/operator-desktop && npm install`).

```bash
cd apps/operator-desktop
npm start
```

Optional: `SAGEO_BOOTSTRAP_PYTHON=/path/to/.venv/bin/python npm start` so
first-run Finish can validate against a known interpreter.

## Operator loop

| Stage | What it does | Bridge / CLI |
| --- | --- | --- |
| Wizard / Settings | Persist checkout root, interpreter, optional `runs_root` | ready-check / session |
| New Run | Collect **Property refs** (`site_url`, optional GSC/GA4), Reach, optional goal; Start `thin_audit` | `start-thin-audit` |
| Progress | Agent checklist, `gate_state`, ~1s refresh while active | `get-progress` |
| Findings | Master–detail Evidence browse; NHV badge + `verification_reason`; filter by confidence / Agent | `list-findings` |
| Review | Paused Agent + Decision log context; Evidence deep-links into Findings; Approve / Reject (Reject confirms); optional `operator_note` | `get-review`, `resume-run` |

Reject stays on Review showing the result. Approve that closes the gate
continues into Progress updates; Approve into another open gate stays on Review.

## Hermetic checks (no Electron window required)

```bash
pytest tests/operator/
cd apps/operator-desktop && npm test
```

Default pytest stubs Agents and does not call live Connectors. Missing GSC/GA4
credentials on Start are warn-and-allow in the desktop (same bridge warnings).

## Related

- National audit composition: [national-audit.md](national-audit.md)
- AFK / gate resume limits: [afk-automation.md](afk-automation.md)
- Glossary: **Property refs**, **Evidence**, **Human review gate**, **Run directory**
