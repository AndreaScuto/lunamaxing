#!/usr/bin/env python3
"""Validate a LunaMaxing state transition log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TRANSITIONS: dict[str, set[str]] = {
    "UNDERSTAND": {"CLASSIFY", "BLOCKED"},
    "CLASSIFY": {"PLAN", "BLOCKED"},
    "PLAN": {"DELEGATE", "FINAL_VALIDATE", "BLOCKED"},
    "DELEGATE": {"EXECUTE", "FINAL_VALIDATE", "BLOCKED"},
    "EXECUTE": {
        "COLLECT",
        "NEEDS_ORCHESTRATOR_DECISION",
        "BLOCKED",
    },
    "NEEDS_ORCHESTRATOR_DECISION": {"PLAN", "RETRY", "BLOCKED"},
    "COLLECT": {"VERIFY", "BLOCKED"},
    "VERIFY": {"INTEGRATE", "RETRY", "BLOCKED"},
    "RETRY": {"EXECUTE", "BLOCKED"},
    "INTEGRATE": {"PLAN", "FINAL_VALIDATE", "BLOCKED"},
    "FINAL_VALIDATE": {"DONE", "BLOCKED"},
    "DONE": set(),
    "BLOCKED": set(),
}
TERMINAL = {"DONE", "BLOCKED"}
KNOWN_STATES = set(TRANSITIONS)


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return emit(args, [f"unable to read JSON: {exc}"])
    states = payload.get("states") if isinstance(payload, dict) else payload
    retry_budget = payload.get("max_retries", 1) if isinstance(payload, dict) else 1
    errors = validate_state_log(states, retry_budget)
    return emit(args, errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def emit(args: argparse.Namespace, errors: list[str]) -> int:
    result = {"ok": not errors, "errors": sorted(set(errors))}
    if args.as_json:
        print(json.dumps(result, indent=2))
    elif errors:
        print("LunaMaxing state-log validation failed:")
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("LunaMaxing state-log validation passed")
    return 1 if errors else 0


def validate_state_log(states: Any, max_retries: Any = 1) -> list[str]:
    if not isinstance(states, list) or not states:
        return ["states must be a non-empty JSON array"]
    errors: list[str] = []
    if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
        errors.append("max_retries must be a non-negative integer")
        max_retries = 1
    for index, state in enumerate(states):
        if state not in KNOWN_STATES:
            errors.append(f"states[{index}] is unknown: {state!r}")
    if states and states[0] != "UNDERSTAND":
        errors.append("state log must start at UNDERSTAND")
    retry_count = sum(state == "RETRY" for state in states)
    if retry_count > max_retries:
        errors.append(
            f"state log has {retry_count} retries; budget is {max_retries}"
        )
    for index, (current, following) in enumerate(zip(states, states[1:])):
        allowed = TRANSITIONS.get(current, set())
        if following not in allowed:
            errors.append(
                f"invalid transition at {index}: {current} -> {following}"
            )
    if states and states[-1] not in TERMINAL:
        errors.append("state log must end at DONE or BLOCKED")
    for index, state in enumerate(states[:-1]):
        if state in TERMINAL:
            errors.append(f"terminal state {state} cannot be followed at index {index}")
    return sorted(set(errors))


if __name__ == "__main__":
    raise SystemExit(main())
