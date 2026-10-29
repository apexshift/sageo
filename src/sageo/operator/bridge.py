"""Operator runtime bridge implementation."""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from sageo.orchestrator import AgentSpec, RunRequest, RunResult, resume, run


@dataclass(frozen=True)
class ReadyCheckResult:
    """Outcome of validating a local SageO runtime for the operator app."""

    ok: bool
    errors: tuple[str, ...]
    checkout_root: Path
    interpreter: Path
    runs_root: Path


@dataclass(frozen=True)
class RunSummary:
    """Sidebar row metadata for one Run under ``runs_root``."""

    run_id: str
    goal: str
    site_host: str
    reach: str | None
    status: str


@dataclass(frozen=True)
class AgentProgress:
    """One Agent row in the Progress checklist."""

    name: str
    status: str


@dataclass(frozen=True)
class ProgressSnapshot:
    """Progress view: ordered Agent checklist + gate fields."""

    run_id: str
    gate_state: str
    paused_agent: str | None
    agents: tuple[AgentProgress, ...]
    empty_schedule: bool


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


def list_runs(runs_root: Path | str) -> list[RunSummary]:
    """List Runs under ``runs_root`` for sidebar rows (most recent first)."""
    root = Path(runs_root)
    if not root.is_dir():
        return []

    rows: list[tuple[float, RunSummary]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        state_path = child / "state.json"
        if not state_path.is_file():
            continue
        try:
            state = _load_state(state_path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        summary = _run_summary_from_state(child.name, state)
        try:
            mtime = state_path.stat().st_mtime
        except OSError:
            mtime = 0.0
        rows.append((mtime, summary))

    rows.sort(key=lambda item: item[0], reverse=True)
    return [summary for _, summary in rows]


def get_progress(runs_root: Path | str, run_id: str) -> ProgressSnapshot:
    """Read a Progress snapshot from the Run ``state.json``."""
    state_path = Path(runs_root) / run_id / "state.json"
    state = _load_state(state_path)
    return _progress_from_state(run_id, state)


def resume_run(
    runs_root: Path | str,
    run_id: str,
    *,
    agents: Sequence[AgentSpec],
    approved: bool,
    observed_at: str,
    operator_note: str | None = None,
) -> RunResult:
    """Approve or reject a Human review gate via Orchestrator ``resume``."""
    return resume(
        run_id,
        agents,
        runs_root=Path(runs_root),
        approved=approved,
        observed_at=observed_at,
        operator_note=operator_note,
    )


def watch_run_progress(
    runs_root: Path | str,
    run_id: str,
    *,
    poll_interval: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[ProgressSnapshot]:
    """Yield Progress snapshots until the Run is idle.

    Observes Run ``state.json`` via mtime changes with a ``poll_interval``
    sleep (default ~1s) while active (``gate_state != closed``). Stops when
    idle. Stdlib-only (no extra FS-watch dependency).
    """
    root = Path(runs_root)
    state_path = root / run_id / "state.json"

    while True:
        snapshot = get_progress(root, run_id)
        yield snapshot
        if snapshot.gate_state == "closed":
            return

        try:
            last_mtime = state_path.stat().st_mtime
        except OSError:
            last_mtime = None

        # Active: wait for state.json mtime change; poll as the refresh cadence.
        while True:
            sleep(poll_interval)
            try:
                mtime = state_path.stat().st_mtime
            except OSError:
                mtime = None
            if (
                mtime is not None
                and last_mtime is not None
                and mtime != last_mtime
            ):
                break
            next_snap = get_progress(root, run_id)
            if (
                next_snap.gate_state != snapshot.gate_state
                or next_snap.paused_agent != snapshot.paused_agent
                or next_snap.agents != snapshot.agents
            ):
                break


def _load_state(state_path: Path) -> dict[str, Any]:
    data = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"state.json must be an object: {state_path}")
    return data


def _progress_from_state(run_id: str, state: Mapping[str, Any]) -> ProgressSnapshot:
    schedule = state.get("schedule") or []
    if not isinstance(schedule, list):
        schedule = []
    status_by_name: dict[str, str] = {}
    for row in state.get("agent_statuses") or []:
        if isinstance(row, Mapping) and row.get("name"):
            status_by_name[str(row["name"])] = str(row.get("status") or "pending")
    agents = tuple(
        AgentProgress(
            name=str(name),
            status=status_by_name.get(str(name), "pending"),
        )
        for name in schedule
    )
    paused = state.get("paused_agent")
    paused_agent = str(paused) if paused else None
    gate_state = str(state.get("gate_state") or "closed")
    if gate_state != "awaiting_approval":
        paused_agent = None
    return ProgressSnapshot(
        run_id=run_id,
        gate_state=gate_state,
        paused_agent=paused_agent,
        agents=agents,
        empty_schedule=len(schedule) == 0,
    )


def _run_summary_from_state(run_id: str, state: Mapping[str, Any]) -> RunSummary:
    request = state.get("request") or {}
    if not isinstance(request, Mapping):
        request = {}
    property_refs = request.get("property_refs") or {}
    if not isinstance(property_refs, Mapping):
        property_refs = {}
    site_url = str(property_refs.get("site_url") or "")
    reach = request.get("reach")
    return RunSummary(
        run_id=run_id,
        goal=str(request.get("goal") or ""),
        site_host=_site_host(site_url),
        reach=str(reach) if reach is not None else None,
        status=_sidebar_status(state),
    )


def _site_host(site_url: str) -> str:
    if not site_url:
        return ""
    parsed = urlparse(site_url)
    return parsed.hostname or parsed.netloc or ""


def _sidebar_status(state: Mapping[str, Any]) -> str:
    gate_state = str(state.get("gate_state") or "closed")
    if gate_state == "awaiting_approval":
        return "awaiting_approval"
    schedule = state.get("schedule") or []
    if not schedule:
        return "ask_human"
    statuses = state.get("agent_statuses") or []
    if any(
        isinstance(row, Mapping) and row.get("status") == "awaiting_human_review"
        for row in statuses
    ):
        return "rejected"
    return "completed"


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
