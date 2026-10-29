"""Operator runtime config persistence and launch gating.

Electron main persists the same JSON shape under its userData path and calls
``validate_runtime`` for ready-check — no parallel validation logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sageo.operator.bridge import ReadyCheckResult, validate_runtime

LaunchView = Literal["wizard", "shell"]


@dataclass(frozen=True)
class RuntimeConfig:
    """Persisted local SageO runtime paths for the operator app."""

    checkout_root: str
    interpreter: str
    runs_root: str | None = None


@dataclass(frozen=True)
class LaunchDecision:
    """Whether to show the first-run wizard or the app shell."""

    view: LaunchView
    config: RuntimeConfig | None
    ready: ReadyCheckResult | None
    errors: tuple[str, ...]


def save_runtime_config(path: Path | str, config: RuntimeConfig) -> None:
    """Write runtime config JSON (Electron userData or test path)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "checkout_root": config.checkout_root,
        "interpreter": config.interpreter,
    }
    if config.runs_root is not None:
        payload["runs_root"] = config.runs_root
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_runtime_config(path: Path | str) -> RuntimeConfig | None:
    """Load runtime config, or None when missing/invalid."""
    target = Path(path)
    if not target.is_file():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    checkout = data.get("checkout_root")
    interpreter = data.get("interpreter")
    if not isinstance(checkout, str) or not checkout.strip():
        return None
    if not isinstance(interpreter, str) or not interpreter.strip():
        return None
    runs_root = data.get("runs_root")
    if runs_root is not None:
        if not isinstance(runs_root, str):
            return None
        # Empty optional override is omitted (same as unset).
        runs_root = runs_root.strip() or None
    return RuntimeConfig(
        checkout_root=checkout.strip(),
        interpreter=interpreter.strip(),
        runs_root=runs_root,
    )


def resolve_launch(config_path: Path | str) -> LaunchDecision:
    """Decide wizard vs shell from saved config + bridge ready-check."""
    config = load_runtime_config(config_path)
    if config is None:
        return LaunchDecision(
            view="wizard",
            config=None,
            ready=None,
            errors=("runtime config missing or invalid",),
        )
    ready = validate_runtime(
        checkout_root=config.checkout_root,
        interpreter=config.interpreter,
        runs_root=config.runs_root,
    )
    if not ready.ok:
        return LaunchDecision(
            view="wizard",
            config=config,
            ready=ready,
            errors=ready.errors,
        )
    return LaunchDecision(
        view="shell",
        config=config,
        ready=ready,
        errors=(),
    )


def finish_wizard(
    config_path: Path | str,
    config: RuntimeConfig,
) -> LaunchDecision:
    """Validate runtime; persist and open shell only when ready-check passes."""
    ready = validate_runtime(
        checkout_root=config.checkout_root,
        interpreter=config.interpreter,
        runs_root=config.runs_root,
    )
    if not ready.ok:
        return LaunchDecision(
            view="wizard",
            config=config,
            ready=ready,
            errors=ready.errors,
        )
    persisted = RuntimeConfig(
        checkout_root=str(ready.checkout_root),
        interpreter=str(ready.interpreter),
        runs_root=str(ready.runs_root),
    )
    save_runtime_config(config_path, persisted)
    return LaunchDecision(
        view="shell",
        config=persisted,
        ready=ready,
        errors=(),
    )
