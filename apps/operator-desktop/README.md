# SageO Operator Desktop

Electron shell over a local SageO checkout + Python interpreter. Main process
calls `python -m sageo.operator` for ready-check and launch decisions (no
parallel validation).

## Develop

```bash
# from repo root, with sageo installed in the interpreter you will select
cd apps/operator-desktop
npm install
npm start
```

Optional bootstrap interpreter for first-run Finish if needed:

```bash
SAGEO_BOOTSTRAP_PYTHON=/path/to/.venv/bin/python npm start
```

## Hermetic checks

- Python session/bridge/Start/Progress: `pytest tests/operator/`
- Main-process config helpers: `npm test` (no Electron window)

New Run Start maps to `python -m sageo.operator start-thin-audit`. Progress
polls `get-progress` (~1s) until `gate_state` is closed.
