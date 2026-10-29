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


def _write_thin_audit_agents(checkout: Path) -> None:
    import yaml

    agents = checkout / "agents"
    for name, gate in (
        ("technical-findings", "not_required"),
        ("content-aio", "required"),
        ("local-reach", "required"),
        ("measurement-evidence", "required"),
    ):
        agent_dir = agents / name
        agent_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "name": name,
            "description": name,
            "metadata": {
                "version": "0.1.0",
                "primary_outcome": "SEO",
                "skills": "alpha-skill",
                "human_review_gate": gate,
                "cost_model": "tokens_only",
            },
        }
        fm = yaml.safe_dump(frontmatter, sort_keys=False).strip()
        (agent_dir / "AGENT.md").write_text(
            f"---\n{fm}\n---\n\n## Purpose\n\nFixture.\n",
            encoding="utf-8",
        )


def test_cli_start_list_progress_flow(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    _write_thin_audit_agents(checkout)
    runs_root = tmp_path / "runs"
    started = _run_cli(
        [
            "start-thin-audit",
            "--checkout-root",
            str(checkout),
            "--runs-root",
            str(runs_root),
            "--site-url",
            "https://example.com/",
            "--reach",
            "local",
            "--run-id",
            "run-cli",
            "--observed-at",
            "2026-10-29T12:00:00+00:00",
        ]
    )
    assert started.returncode == 0
    start_payload = json.loads(started.stdout)
    assert start_payload["run_id"] == "run-cli"
    assert start_payload["gate_state"] == "awaiting_approval"
    assert [a["name"] for a in start_payload["progress"]["agents"]] == [
        "technical-findings",
        "content-aio",
        "local-reach",
        "measurement-evidence",
    ]

    listed = _run_cli(["list-runs", "--runs-root", str(runs_root)])
    assert listed.returncode == 0
    rows = json.loads(listed.stdout)
    assert rows[0]["run_id"] == "run-cli"
    assert rows[0]["status"] == "awaiting_approval"

    progress = _run_cli(
        ["get-progress", "--runs-root", str(runs_root), "--run-id", "run-cli"]
    )
    assert progress.returncode == 0
    snap = json.loads(progress.stdout)
    assert snap["paused_agent"] == "content-aio"
