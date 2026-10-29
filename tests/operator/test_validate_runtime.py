"""Operator bridge black-box: validate local SageO runtime ready-check."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sageo.operator import validate_runtime


def _checkout_layout(root: Path, *, with_orchestrator: bool = True, with_agents: bool = True) -> Path:
    checkout = root / "sageo-checkout"
    checkout.mkdir()
    if with_orchestrator:
        (checkout / "orchestrator").mkdir()
        (checkout / "orchestrator" / "ORCHESTRATOR.md").write_text("# stub\n", encoding="utf-8")
    if with_agents:
        (checkout / "agents").mkdir()
        (checkout / "agents" / ".keep").write_text("", encoding="utf-8")
    return checkout


def test_validate_runtime_ready_with_default_runs_root(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    result = validate_runtime(
        checkout_root=checkout,
        interpreter=Path(sys.executable),
    )
    assert result.ok is True
    assert result.errors == ()
    assert result.runs_root == checkout / "runs"
    assert result.checkout_root == checkout.resolve()
    assert result.interpreter == Path(sys.executable).absolute()


def test_validate_runtime_ready_with_runs_root_override(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    override = tmp_path / "custom-runs"
    result = validate_runtime(
        checkout_root=checkout,
        interpreter=Path(sys.executable),
        runs_root=override,
    )
    assert result.ok is True
    assert result.errors == ()
    assert result.runs_root == override.resolve()


def test_validate_runtime_missing_orchestrator_returns_specific_error(
    tmp_path: Path,
) -> None:
    checkout = _checkout_layout(tmp_path, with_orchestrator=False)
    result = validate_runtime(
        checkout_root=checkout,
        interpreter=Path(sys.executable),
    )
    assert result.ok is False
    assert any("orchestrator" in err.lower() for err in result.errors)
    assert result.runs_root == checkout / "runs"


def test_validate_runtime_missing_agents_returns_specific_error(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path, with_agents=False)
    result = validate_runtime(
        checkout_root=checkout,
        interpreter=Path(sys.executable),
    )
    assert result.ok is False
    assert any("agents" in err.lower() for err in result.errors)


def test_validate_runtime_interpreter_cannot_import_sageo(tmp_path: Path) -> None:
    checkout = _checkout_layout(tmp_path)
    # A non-Python binary (or missing path) cannot import sageo.
    bad_interpreter = tmp_path / "not-a-python"
    bad_interpreter.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    bad_interpreter.chmod(0o755)
    result = validate_runtime(
        checkout_root=checkout,
        interpreter=bad_interpreter,
    )
    assert result.ok is False
    assert any("sageo" in err.lower() for err in result.errors)


def test_validate_runtime_does_not_require_connector_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = _checkout_layout(tmp_path)
    for key in (
        "GSC_CREDENTIALS_JSON",
        "GA4_CREDENTIALS_JSON",
        "CRAWL_SERP_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        monkeypatch.delenv(key, raising=False)
    result = validate_runtime(
        checkout_root=checkout,
        interpreter=Path(sys.executable),
    )
    assert result.ok is True
    assert result.errors == ()
