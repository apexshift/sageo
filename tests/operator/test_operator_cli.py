"""Hermetic CLI for Electron main: validate / resolve-launch / finish-wizard."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _checkout_layout(root: Path) -> Path:
    checkout = root / "sageo-checkout"
    checkout.mkdir()
    (checkout / "orchestrator").mkdir()
    (checkout / "agents").mkdir()
    return checkout


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sageo.operator", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_validate_ok_json(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    completed = _run_cli(
        [
            "validate",
            "--checkout-root",
            str(checkout),
            "--interpreter",
            sys.executable,
        ]
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["errors"] == []


def test_cli_resolve_launch_missing_config(tmp_path: Path) -> None:
    completed = _run_cli(
        ["resolve-launch", "--config-path", str(tmp_path / "runtime.json")]
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["view"] == "wizard"


def test_cli_finish_wizard_persists(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    config_path = tmp_path / "runtime.json"
    completed = _run_cli(
        [
            "finish-wizard",
            "--config-path",
            str(config_path),
            "--checkout-root",
            str(checkout),
            "--interpreter",
            sys.executable,
        ]
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["view"] == "shell"
    assert config_path.is_file()
