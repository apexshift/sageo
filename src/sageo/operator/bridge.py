"""Operator runtime bridge implementation."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sageo.orchestrator import AgentSpec, RunRequest, RunResult, run


@dataclass(frozen=True)
class ReadyCheckResult:
    """Outcome of validating a local SageO runtime for the operator app."""

    ok: bool
    errors: tuple[str, ...]
    checkout_root: Path
    interpreter: Path
    runs_root: Path


def validate_runtime(
    *,
    checkout_root: Path | str,
    interpreter: Path | str,
    runs_root: Path | str | None = None,
) -> ReadyCheckResult:
    """Ready-check checkout layout and interpreter ``import sageo``.

    Connector credentials are not required. ``runs_root`` defaults to
    ``<checkout>/runs`` when omitted.
    """
    checkout = Path(checkout_root).expanduser().resolve()
    # Keep the venv entrypoint: resolve() follows symlinks and can drop
    # site-packages when interpreter is `.venv/bin/python`.
    interp = Path(interpreter).expanduser().absolute()
    resolved_runs = (
        Path(runs_root).expanduser().resolve()
        if runs_root is not None
        else checkout / "runs"
    )

    errors: list[str] = []
    orchestrator_dir = checkout / "orchestrator"
    if not orchestrator_dir.is_dir():
        errors.append(
            f"checkout missing orchestrator/ directory: {orchestrator_dir}"
        )
    agents_dir = checkout / "agents"
    if not agents_dir.is_dir():
        errors.append(f"checkout missing agents/ directory: {agents_dir}")

    import_error = _interpreter_import_sageo_error(interp)
    if import_error is not None:
        errors.append(import_error)

    return ReadyCheckResult(
        ok=not errors,
        errors=tuple(errors),
        checkout_root=checkout,
        interpreter=interp,
        runs_root=resolved_runs,
    )


def start_thin_audit_run(
    *,
    runs_root: Path | str,
    site_url: str,
    agents: Sequence[AgentSpec],
    observed_at: str,
    reach: str = "national",
    goal: str | None = None,
    gsc_property: str | None = None,
    ga4_property: str | None = None,
    run_id: str | None = None,
) -> RunResult:
    """Start a thin_audit Run from the locked New Run field model.

    Derived request fields: ``playbook=thin_audit``, ``intent=thin_audit``,
    ``primary_outcome=SEO``. Empty optional Property refs are omitted.
    When ``goal`` is omitted or blank, synthesize
    ``thin_audit {site_url} ({reach})``.
    """
    site = site_url.strip()
    if not site:
        raise ValueError("site_url is required")

    property_refs: dict[str, str] = {"site_url": site}
    gsc = _optional_ref(gsc_property)
    if gsc is not None:
        property_refs["gsc_property"] = gsc
    ga4 = _optional_ref(ga4_property)
    if ga4 is not None:
        property_refs["ga4_property"] = ga4

    reach_value = (reach or "national").strip() or "national"
    goal_text = (goal or "").strip() or f"thin_audit {site} ({reach_value})"

    request = RunRequest(
        goal=goal_text,
        intent="thin_audit",
        primary_outcome="SEO",
        property_refs=property_refs,
        reach=reach_value,
        playbook="thin_audit",
    )
    return run(
        request,
        agents,
        runs_root=Path(runs_root),
        observed_at=observed_at,
        run_id=run_id,
    )


def _optional_ref(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _interpreter_import_sageo_error(interpreter: Path) -> str | None:
    """Return an error message when ``interpreter`` cannot ``import sageo``."""
    if not interpreter.is_file():
        return f"interpreter cannot import sageo: {interpreter} (not a file)"
    try:
        completed = subprocess.run(
            [str(interpreter), "-c", "import sageo"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError as exc:
        return f"interpreter cannot import sageo: {interpreter} ({exc})"
    if completed.returncode == 0:
        return None
    detail = (completed.stderr or completed.stdout or "").strip()
    if detail:
        return f"interpreter cannot import sageo: {interpreter} ({detail})"
    return f"interpreter cannot import sageo: {interpreter}"
