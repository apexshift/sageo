"""Skill selection for the technical-findings Agent.

Applies AGENT.md conditions: invoke crawl → indexability → schema → CWV,
skipping ``cwv-scorer`` when lab-metrics input is absent.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def select_skills(
    declared: Sequence[str],
    inputs: Mapping[str, Any],
) -> list[str]:
    """Return declared Skills to run for this input set (declared order)."""
    if inputs.get("lab_metrics"):
        return list(declared)
    return [name for name in declared if name != "cwv-scorer"]
