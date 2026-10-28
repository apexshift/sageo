"""Skill selection for the measurement-evidence Agent.

Applies AGENT.md conditions: mention screener only when a corpus is present;
always run severity-impact-scorer then evidence-packager last (declared order).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def select_skills(
    declared: Sequence[str],
    inputs: Mapping[str, Any],
) -> list[str]:
    """Return declared Skills to run for this input set (declared order)."""
    if inputs.get("corpus"):
        return list(declared)
    return [name for name in declared if name != "mention-sentiment-screener"]
