"""Load recorded HTTP request/response fixtures for hermetic Connector tests.

Fixture directory layout (one JSON file per exchange)::

    http/
      search_analytics.json   # {"request": {...}, "response": {...}}
      auth_failed.json

Default pytest/CI must never open a live network socket; packs replay these
exchanges instead of calling Google or DataForSEO.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RecordedExchange:
    """One recorded HTTP request/response pair."""

    name: str
    request: Mapping[str, Any]
    response: Mapping[str, Any]


def load_recorded_http(fixture_dir: Path) -> dict[str, RecordedExchange]:
    """Load all ``*.json`` exchanges from ``fixture_dir``, keyed by stem.

    Each file must contain top-level ``request`` and ``response`` objects.
    Raises ``FileNotFoundError`` if the directory is missing; ``ValueError``
    if an exchange file is malformed.
    """
    if not fixture_dir.is_dir():
        raise FileNotFoundError(
            f"recorded HTTP fixture directory not found: {fixture_dir}"
        )

    exchanges: dict[str, RecordedExchange] = {}
    for path in sorted(fixture_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(
                f"{path.name}: recorded exchange must be a JSON object "
                f"with request and response"
            )
        if "request" not in payload or "response" not in payload:
            raise ValueError(
                f"{path.name}: recorded exchange must include request and response"
            )
        exchanges[path.stem] = RecordedExchange(
            name=path.stem,
            request=payload["request"],
            response=payload["response"],
        )
    return exchanges
