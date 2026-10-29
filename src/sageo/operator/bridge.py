"""Operator runtime bridge implementation."""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Callable, Iterator, Mapping as MappingABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

import yaml

from sageo.orchestrator import AgentSpec, RunRequest, RunResult, resume, run

# Locked thin_audit roster: AGENT.md directory name → Orchestrator pipeline_role.
THIN_AUDIT_PIPELINE_ROLES: Mapping[str, str] = {
    "technical-findings": "technical",
    "content-aio": "content_aio",
    "local-reach": "local_reach",
    "measurement-evidence": "measurement",
}

GSC_CREDENTIAL_KEYS: tuple[str, ...] = (
    "GSC_CLIENT_EMAIL",
    "GSC_PRIVATE_KEY",
    "GSC_PROPERTY_URL",
)
GA4_CREDENTIAL_KEYS: tuple[str, ...] = (
    "GA4_PROPERTY_ID",
    "GA4_CREDENTIALS_JSON",
)


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


@dataclass(frozen=True)
class StartThinAuditResult:
    """Outcome of starting a thin_audit Run from the operator New Run form."""

    run_id: str
    run_dir: Path
    gate_state: str
    warnings: tuple[str, ...]
    result: RunResult


@dataclass(frozen=True)
class FindingRow:
    """One Evidence row for the Findings master–detail list."""

    id: str
    title: str
    agent: str
    confidence: str
    claim: str
    source: str
    method: str | None
    observed_at: str
    verification_reason: str | None
    is_nhv: bool


@dataclass(frozen=True)
class ReviewSnapshot:
    """Review stage: Human review gate context or empty copy."""

    run_id: str
    gate_state: str
    paused_agent: str | None
    gate_open: bool
    empty_message: str | None
    decision: dict[str, Any] | None
    evidence_ids: tuple[str, ...]
    linked_findings: tuple[FindingRow, ...]


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


def connector_credential_warnings(
    *,
    gsc_property: str | None,
    ga4_property: str | None,
    env: Mapping[str, str | None] | None = None,
) -> tuple[str, ...]:
    """Warn (do not block) when Connector property ids lack env credentials."""
    environ: MappingABC[str, str | None]
    if env is None:
        environ = os.environ
    else:
        environ = env
    warnings: list[str] = []
    gsc = _optional_ref(gsc_property)
    if gsc is not None and not _env_has_all(environ, GSC_CREDENTIAL_KEYS):
        warnings.append(
            "GSC property set without Connector credentials; Start allowed — "
            "Skills may emit needs_human_verification Evidence."
        )
    ga4 = _optional_ref(ga4_property)
    if ga4 is not None and not _env_has_all(environ, GA4_CREDENTIAL_KEYS):
        warnings.append(
            "GA4 property set without Connector credentials; Start allowed — "
            "Skills may emit needs_human_verification Evidence."
        )
    return tuple(warnings)


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


def start_thin_audit_from_checkout(
    *,
    checkout_root: Path | str,
    runs_root: Path | str,
    site_url: str,
    observed_at: str,
    reach: str = "national",
    goal: str | None = None,
    gsc_property: str | None = None,
    ga4_property: str | None = None,
    run_id: str | None = None,
    env: Mapping[str, str | None] | None = None,
) -> StartThinAuditResult:
    """Start thin_audit using Agent packages under ``checkout_root/agents``.

    Agent ``execute`` callables are hermetic placeholders (no live Skills).
    ``human_review_gate`` is read from each AGENT.md so Progress/gates match
    the shipped contracts. Returns credential warnings without blocking Start.
    """
    warnings = connector_credential_warnings(
        gsc_property=gsc_property,
        ga4_property=ga4_property,
        env=env,
    )
    agents = load_thin_audit_agents(Path(checkout_root))
    result = start_thin_audit_run(
        runs_root=runs_root,
        site_url=site_url,
        agents=agents,
        observed_at=observed_at,
        reach=reach,
        goal=goal,
        gsc_property=gsc_property,
        ga4_property=ga4_property,
        run_id=run_id,
    )
    return StartThinAuditResult(
        run_id=result.run_id,
        run_dir=result.run_dir,
        gate_state=result.gate_state,
        warnings=warnings,
        result=result,
    )


def load_thin_audit_agents(checkout_root: Path | str) -> list[AgentSpec]:
    """Build thin_audit AgentSpecs from ``agents/`` under the checkout."""
    agents_root = Path(checkout_root) / "agents"
    loaded: list[AgentSpec] = []
    for name, role in THIN_AUDIT_PIPELINE_ROLES.items():
        agent_dir = agents_root / name
        agent_md = agent_dir / "AGENT.md"
        if not agent_md.is_file():
            continue
        meta = _agent_metadata(agent_md)
        gate = str(meta.get("human_review_gate") or "not_required")
        if gate not in {"required", "not_required"}:
            gate = "not_required"
        primary = str(meta.get("primary_outcome") or "SEO")

        def _execute(
            ctx: Mapping[str, Any], *, _name: str = name
        ) -> dict[str, Any]:
            evidence_id = f"{_name}-ev"
            observed = str(ctx.get("observed_at") or "")
            return {
                "evidence_ids": [evidence_id],
                "evidence": [
                    {
                        "id": evidence_id,
                        "claim": f"{_name} finding",
                        "source": f"agent:{_name}",
                        "observed_at": observed,
                        "confidence": "high",
                        "agent": _name,
                    }
                ],
                "status": "completed",
            }

        loaded.append(
            AgentSpec(
                name=name,
                primary_outcome=primary,
                when_to_use=frozenset({"thin_audit"}),
                human_review_gate=gate,  # type: ignore[arg-type]
                pipeline_role=role,  # type: ignore[arg-type]
                execute=_execute,
            )
        )
    if not loaded:
        raise ValueError(
            f"no thin_audit Agents found under {agents_root} "
            f"(expected one of {sorted(THIN_AUDIT_PIPELINE_ROLES)})"
        )
    return loaded


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


def list_findings(
    runs_root: Path | str,
    run_id: str,
    *,
    confidence: str | None = None,
    agent: str | None = None,
) -> list[FindingRow]:
    """List Evidence rows for Findings (default: show all)."""
    run_dir = Path(runs_root) / run_id
    rows = [_finding_from_evidence(item) for item in _load_evidence_rows(run_dir)]
    conf = (confidence or "").strip()
    if conf in {"nhv", "needs_human_verification"}:
        rows = [row for row in rows if row.is_nhv]
    elif conf:
        rows = [row for row in rows if row.confidence == conf]
    agent_filter = (agent or "").strip()
    if agent_filter:
        rows = [row for row in rows if row.agent == agent_filter]
    return rows


def get_review(runs_root: Path | str, run_id: str) -> ReviewSnapshot:
    """Review snapshot: gate context + linked Evidence, or empty copy."""
    run_dir = Path(runs_root) / run_id
    state = _load_state(run_dir / "state.json")
    gate_state = str(state.get("gate_state") or "closed")
    paused = state.get("paused_agent")
    paused_agent = str(paused) if paused else None
    gate_open = gate_state == "awaiting_approval"
    if not gate_open:
        return ReviewSnapshot(
            run_id=run_id,
            gate_state=gate_state,
            paused_agent=None,
            gate_open=False,
            empty_message="No Human review gate is open for this Run.",
            decision=None,
            evidence_ids=(),
            linked_findings=(),
        )

    decision = _latest_gate_stop_decision(run_dir)
    evidence_ids = tuple(
        str(eid)
        for eid in (decision or {}).get("evidence_ids")
        or state.get("evidence_refs")
        or []
    )
    all_findings = list_findings(runs_root, run_id)
    id_set = set(evidence_ids)
    linked = tuple(row for row in all_findings if row.id in id_set)
    return ReviewSnapshot(
        run_id=run_id,
        gate_state=gate_state,
        paused_agent=paused_agent,
        gate_open=True,
        empty_message=None,
        decision=decision,
        evidence_ids=evidence_ids,
        linked_findings=linked,
    )


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


def resume_run_from_checkout(
    *,
    checkout_root: Path | str,
    runs_root: Path | str,
    run_id: str,
    approved: bool,
    observed_at: str,
    operator_note: str | None = None,
) -> RunResult:
    """Resume a gate using thin_audit Agents loaded from the checkout."""
    agents = load_thin_audit_agents(Path(checkout_root))
    return resume_run(
        runs_root,
        run_id,
        agents=agents,
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


def _load_evidence_rows(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "evidence.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _finding_from_evidence(item: Mapping[str, Any]) -> FindingRow:
    claim = str(item.get("claim") or "")
    confidence = str(item.get("confidence") or "")
    is_nhv = confidence == "needs_human_verification"
    reason = item.get("verification_reason")
    method = item.get("method")
    evidence_id = str(item.get("id") or item.get("evidence_id") or claim or "unknown")
    agent = str(item.get("agent") or "unknown")
    return FindingRow(
        id=evidence_id,
        title=claim or evidence_id,
        agent=agent,
        confidence=confidence,
        claim=claim,
        source=str(item.get("source") or ""),
        method=str(method) if method is not None else None,
        observed_at=str(item.get("observed_at") or ""),
        verification_reason=str(reason) if reason is not None else None,
        is_nhv=is_nhv,
    )


def _latest_gate_stop_decision(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "decision_log.jsonl"
    if not path.is_file():
        return None
    latest: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") != "gate":
            continue
        outcome = entry.get("outcome")
        human = entry.get("human_review")
        if outcome == "awaiting_approval" or human == "awaiting_approval":
            latest = entry
    return latest


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


def _env_has_all(
    env: MappingABC[str, str | None], keys: Sequence[str]
) -> bool:
    return all((env.get(key) or "").strip() for key in keys)


def _agent_metadata(agent_md: Path) -> dict[str, Any]:
    text = agent_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"AGENT.md YAML frontmatter is required: {agent_md}")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise ValueError(f"AGENT.md YAML frontmatter is required: {agent_md}")
    data = yaml.safe_load(rest[:end])
    if not isinstance(data, dict):
        raise ValueError(f"AGENT.md frontmatter must be a mapping: {agent_md}")
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        return {}
    return meta


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
