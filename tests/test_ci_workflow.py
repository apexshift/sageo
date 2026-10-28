"""CI workflow seam: hermetic Actions config matches the locked P5 shape."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists_with_pr_and_main_triggers() -> None:
    assert WORKFLOW.is_file(), "expected .github/workflows/ci.yml"
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    # GitHub Actions may parse `on` as boolean True in YAML 1.1.
    triggers = doc.get("on") or doc.get(True)
    assert isinstance(triggers, dict)
    assert "pull_request" in triggers
    push = triggers.get("push")
    assert isinstance(push, dict)
    assert "main" in list(push.get("branches") or [])


def test_ci_workflow_runs_lint_contract_lint_and_pytest_without_secrets() -> None:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs = doc.get("jobs") or {}
    assert jobs, "expected at least one CI job"

    combined = yaml.dump(doc).lower()
    assert "secrets." not in combined
    assert "make ci" in combined or (
        "lint" in combined and "contract" in combined and "pytest" in combined
    )

    # Prefer a single hermetic job that installs deps then runs the local CI script.
    job = next(iter(jobs.values()))
    steps = job.get("steps") or []
    step_text = "\n".join(
        str(step.get("run") or step.get("uses") or "") for step in steps
    ).lower()
    assert "checkout" in step_text or any(
        "actions/checkout" in str(step.get("uses") or "") for step in steps
    )
    assert "pip install" in step_text or "pip install" in combined
    assert "make ci" in step_text or (
        "lint" in step_text and "contract" in step_text and ("pytest" in step_text or "test" in step_text)
    )
