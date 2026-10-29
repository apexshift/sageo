"""Operator session: persist runtime config and launch wizard vs shell."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sageo.operator import (
    RuntimeConfig,
    finish_wizard,
    load_runtime_config,
    resolve_launch,
    save_runtime_config,
)


def _checkout_layout(root: Path) -> Path:
    checkout = root / "sageo-checkout"
    checkout.mkdir()
    (checkout / "orchestrator").mkdir()
    (checkout / "agents").mkdir()
    return checkout


def test_save_and_load_runtime_config_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    config = RuntimeConfig(
        checkout_root=str(tmp_path / "checkout"),
        interpreter=str(tmp_path / "python"),
        runs_root=str(tmp_path / "runs"),
    )
    save_runtime_config(path, config)
    loaded = load_runtime_config(path)
    assert loaded == config


def test_load_runtime_config_missing_returns_none(tmp_path: Path) -> None:
    assert load_runtime_config(tmp_path / "missing.json") is None


def test_load_runtime_config_invalid_json_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    path.write_text("{not-json", encoding="utf-8")
    assert load_runtime_config(path) is None


def test_load_runtime_config_missing_required_fields_returns_none(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps({"checkout_root": "/x"}), encoding="utf-8")
    assert load_runtime_config(path) is None


def test_resolve_launch_missing_config_shows_wizard(tmp_path: Path) -> None:
    decision = resolve_launch(tmp_path / "runtime.json")
    assert decision.view == "wizard"
    assert decision.config is None
    assert decision.ready is None
    assert any("missing" in err.lower() or "invalid" in err.lower() for err in decision.errors)


def test_resolve_launch_invalid_saved_config_shows_wizard(tmp_path: Path) -> None:
    checkout = tmp_path / "broken-checkout"
    checkout.mkdir()
    path = tmp_path / "runtime.json"
    save_runtime_config(
        path,
        RuntimeConfig(
            checkout_root=str(checkout),
            interpreter=sys.executable,
        ),
    )
    decision = resolve_launch(path)
    assert decision.view == "wizard"
    assert decision.config is not None
    assert decision.ready is not None
    assert decision.ready.ok is False
    assert decision.errors == decision.ready.errors
    assert any("orchestrator" in err.lower() or "agents" in err.lower() for err in decision.errors)


def test_resolve_launch_valid_config_shows_shell(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    path = tmp_path / "runtime.json"
    save_runtime_config(
        path,
        RuntimeConfig(
            checkout_root=str(checkout),
            interpreter=sys.executable,
        ),
    )
    decision = resolve_launch(path)
    assert decision.view == "shell"
    assert decision.errors == ()
    assert decision.ready is not None
    assert decision.ready.ok is True
    assert decision.ready.runs_root == checkout.resolve() / "runs"


def test_finish_wizard_blocked_when_ready_check_fails(tmp_path: Path) -> None:
    path = tmp_path / "runtime.json"
    decision = finish_wizard(
        path,
        RuntimeConfig(
            checkout_root=str(tmp_path / "empty"),
            interpreter=sys.executable,
        ),
    )
    assert decision.view == "wizard"
    assert decision.ready is not None
    assert decision.ready.ok is False
    assert decision.errors
    assert load_runtime_config(path) is None


def test_finish_wizard_persists_and_opens_shell_when_ready(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    path = tmp_path / "runtime.json"
    override = tmp_path / "custom-runs"
    decision = finish_wizard(
        path,
        RuntimeConfig(
            checkout_root=str(checkout),
            interpreter=sys.executable,
            runs_root=str(override),
        ),
    )
    assert decision.view == "shell"
    assert decision.errors == ()
    loaded = load_runtime_config(path)
    assert loaded is not None
    assert Path(loaded.checkout_root) == checkout.resolve()
    assert loaded.interpreter == str(Path(sys.executable).absolute())
    assert Path(loaded.runs_root) == override.resolve()
