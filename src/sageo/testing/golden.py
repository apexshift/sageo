"""Shared helpers for Skill-package golden tests.

Other Core Skill tickets import these helpers so each package does not
re-implement Evidence schema checks or script loading.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator


def require_evidence_schema(skill_test_root: Path) -> Path:
    """Return ``evidence.schema.json`` under the Skill's test root, or raise."""
    schema_path = skill_test_root / "evidence.schema.json"
    if not schema_path.is_file():
        raise FileNotFoundError(
            f"evidence.schema.json is required under {skill_test_root}"
        )
    return schema_path


def load_skill_module(script_path: Path, module_name: str) -> ModuleType:
    """Load a Skill ``scripts/*.py`` file as a module (hermetic, no package install)."""
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load skill script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_evidence_matches_schema(
    evidence: Sequence[Mapping[str, Any]],
    schema_path: Path,
) -> None:
    """Validate ``evidence`` against the Skill's ``evidence.schema.json``."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(list(evidence)), key=lambda e: e.path)
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise AssertionError(f"Evidence failed schema {schema_path.name}: {messages}")
