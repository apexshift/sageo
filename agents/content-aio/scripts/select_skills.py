"""Skill selection for the content-aio Agent.

Applies AGENT.md conditions: intent → extractability → entity → citation,
skipping ``citation-opportunity-identifier`` when authority inputs are absent.
Citation opportunities remain white-hat only (enforced by the Skill contract).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def select_skills(
    declared: Sequence[str],
    inputs: Mapping[str, Any],
) -> list[str]:
    """Return declared Skills to run for this input set (declared order)."""
    if inputs.get("authority_inputs"):
        return list(declared)
    return [name for name in declared if name != "citation-opportunity-identifier"]
