"""CLI for Electron main: JSON ready-check and launch decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sageo.operator.bridge import ReadyCheckResult, validate_runtime
from sageo.operator.session import (
    RuntimeConfig,
    finish_wizard,
    resolve_launch,
)


def _ready_dict(ready: ReadyCheckResult | None) -> dict[str, Any] | None:
    if ready is None:
        return None
    return {
        "ok": ready.ok,
        "errors": list(ready.errors),
        "checkout_root": str(ready.checkout_root),
        "interpreter": str(ready.interpreter),
        "runs_root": str(ready.runs_root),
    }


def _decision_dict(decision: Any) -> dict[str, Any]:
    config = decision.config
    return {
        "view": decision.view,
        "errors": list(decision.errors),
        "config": None
        if config is None
        else {
            "checkout_root": config.checkout_root,
            "interpreter": config.interpreter,
            "runs_root": config.runs_root,
        },
        "ready": _ready_dict(decision.ready),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sageo.operator")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate", help="Run bridge validate_runtime")
    validate_p.add_argument("--checkout-root", required=True)
    validate_p.add_argument("--interpreter", required=True)
    validate_p.add_argument("--runs-root", default=None)

    resolve_p = sub.add_parser("resolve-launch", help="Wizard vs shell decision")
    resolve_p.add_argument("--config-path", required=True)

    finish_p = sub.add_parser("finish-wizard", help="Validate, persist, open shell")
    finish_p.add_argument("--config-path", required=True)
    finish_p.add_argument("--checkout-root", required=True)
    finish_p.add_argument("--interpreter", required=True)
    finish_p.add_argument("--runs-root", default=None)

    args = parser.parse_args(argv)

    if args.command == "validate":
        ready = validate_runtime(
            checkout_root=args.checkout_root,
            interpreter=args.interpreter,
            runs_root=args.runs_root,
        )
        json.dump(_ready_dict(ready), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if ready.ok else 1

    if args.command == "resolve-launch":
        decision = resolve_launch(Path(args.config_path))
        json.dump(_decision_dict(decision), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if decision.view == "shell" else 1

    if args.command == "finish-wizard":
        decision = finish_wizard(
            Path(args.config_path),
            RuntimeConfig(
                checkout_root=args.checkout_root,
                interpreter=args.interpreter,
                runs_root=args.runs_root,
            ),
        )
        json.dump(_decision_dict(decision), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if decision.view == "shell" else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
