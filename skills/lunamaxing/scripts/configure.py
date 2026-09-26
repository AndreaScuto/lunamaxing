#!/usr/bin/env python3
"""Create, validate, and resolve LunaMaxing model-routing configuration."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Iterable

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SKILL_ROOT / "assets" / "lunamaxing.example.json"
try:
    from .roles import AGENT_ROLES, ROLE_ALIASES
except ImportError:
    # Support both direct CLI execution and loading this file as a standalone module.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from roles import AGENT_ROLES, ROLE_ALIASES
    finally:
        sys.path.pop(0)
REASONING_EFFORTS = {
    "inherit",
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "ultra",
}
DELEGATION_MODES = {"conservative", "balanced", "eager"}
TOP_LEVEL_FIELDS = {"$schema", "orchestrator", "agents", "delegation"}
MODEL_FIELDS = {"model", "reasoning_effort"}
DELEGATION_FIELDS = {
    "mode",
    "max_workers",
    "max_retries_per_packet",
}
OBSOLETE_DELEGATION_FIELDS = {
    "min_workers_nontrivial": (
        "remove it; non-trivial tasks are decomposed automatically, and max_workers "
        "can cap parallelism"
    ),
    "target_workers_complex": (
        "remove it; worker count is selected per task, and max_workers can cap parallelism"
    ),
    "decompose_before_local": "remove it; decomposition now happens before local implementation",
}


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            return init_config(args.path)
        if args.command == "interactive":
            return interactive_config(args.path)
        source = load_json(args.path) if args.path.is_file() else {}
        if args.command == "validate":
            if not args.path.is_file():
                raise ValueError(f"configuration file not found: {args.path}")
            errors = validate_config(source)
            return emit_validation(errors)
        resolved = resolve_config(source, args.overrides)
        if args.command == "spawn":
            print(json.dumps(spawn_settings(resolved, args.role), indent=2))
        else:
            print(json.dumps(resolved, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"LunaMaxing configuration error: {exc}")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create .lunamaxing.json")
    init_parser.add_argument("path", nargs="?", type=Path, default=Path(".lunamaxing.json"))

    interactive_parser = subparsers.add_parser(
        "interactive", help="interactively create or edit a configuration"
    )
    interactive_parser.add_argument("path", nargs="?", type=Path, default=Path(".lunamaxing.json"))

    validate_parser = subparsers.add_parser("validate", help="validate a config file")
    validate_parser.add_argument("path", nargs="?", type=Path, default=Path(".lunamaxing.json"))

    resolve_parser = subparsers.add_parser("resolve", help="print merged effective config")
    resolve_parser.add_argument("path", nargs="?", type=Path, default=Path(".lunamaxing.json"))
    resolve_parser.add_argument("--set", dest="overrides", action="append", default=[])

    spawn_parser = subparsers.add_parser("spawn", help="print explicit spawn settings for a role")
    spawn_parser.add_argument(
        "role", choices=("orchestrator", *AGENT_ROLES, *ROLE_ALIASES)
    )
    spawn_parser.add_argument("path", nargs="?", type=Path, default=Path(".lunamaxing.json"))
    spawn_parser.add_argument("--set", dest="overrides", action="append", default=[])

    return parser.parse_args()


def init_config(path: Path) -> int:
    if path.exists():
        raise ValueError(f"refusing to overwrite existing configuration: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"LunaMaxing configuration written to {path}")
    return 0


def interactive_config(path: Path) -> int:
    exists = path.exists()
    source = load_json(path) if exists else {}
    delegation = source.get("delegation")
    if isinstance(delegation, dict):
        for field, advice in OBSOLETE_DELEGATION_FIELDS.items():
            if field in delegation:
                print(
                    f"Obsolete delegation.{field}; {advice}. "
                    "It will be removed only if you confirm."
                )
                del delegation[field]
    current = resolve_config(source)
    updated = copy.deepcopy(current)

    for role in ("orchestrator", *AGENT_ROLES):
        selected = (
            updated["orchestrator"]
            if role == "orchestrator"
            else updated["agents"][role]
        )
        selected["model"] = prompt_model(role, selected["model"])
        selected["reasoning_effort"] = prompt_effort(role, selected["reasoning_effort"])

    errors = validate_config(updated)
    if errors:
        raise ValueError("; ".join(errors))

    print("\nConfiguration summary:")
    for role in ("orchestrator", *AGENT_ROLES):
        selected = (
            updated["orchestrator"]
            if role == "orchestrator"
            else updated["agents"][role]
        )
        print(f"  {role}: {selected['model']} / {selected['reasoning_effort']}")

    if exists and input(f"Overwrite {path}? [y/N] ").strip().lower() not in {
        "y",
        "yes",
    }:
        print("Configuration unchanged.")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    print(f"LunaMaxing configuration written to {path}")
    return 0


def prompt_model(role: str, current: str) -> str:
    while True:
        value = input(
            f"{role} model [{current}] (Enter=keep, inherit, or model ID): "
        ).strip()
        if not value or value.lower() in {"current", "keep"}:
            return current
        if value.lower() == "inherit":
            return "inherit"
        if value:
            return value


def prompt_effort(role: str, current: str) -> str:
    choices = (
        "inherit",
        "none",
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    )
    while True:
        value = input(
            f"{role} reasoning_effort [{current}] "
            f"(Enter=keep; {', '.join(choices)}): "
        ).strip().lower()
        if not value or value in {"current", "keep"}:
            return current
        if value in REASONING_EFFORTS:
            return value
        print(f"Invalid reasoning effort. Choose one of: {', '.join(choices)}")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("configuration must be a JSON object")
    return payload


def default_config() -> dict[str, Any]:
    return load_json(DEFAULT_CONFIG_PATH)


def resolve_config(
    config: dict[str, Any] | None,
    overrides: Iterable[str] = (),
) -> dict[str, Any]:
    config = config or {}
    errors = validate_config(config)
    if errors:
        raise ValueError("; ".join(errors))
    resolved = deep_merge(default_config(), config)
    for override in overrides:
        apply_override(resolved, override)
    errors = validate_config(resolved)
    if errors:
        raise ValueError("; ".join(errors))
    return resolved


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def apply_override(config: dict[str, Any], expression: str) -> None:
    if "=" not in expression:
        raise ValueError(f"override must use path=value: {expression}")
    raw_path, raw_value = expression.split("=", 1)
    parts = [part for part in raw_path.split(".") if part]
    if not parts:
        raise ValueError(f"override path is empty: {expression}")
    target: Any = config
    for part in parts[:-1]:
        if not isinstance(target, dict) or part not in target:
            raise ValueError(f"unknown override path: {raw_path}")
        target = target[part]
    leaf = parts[-1]
    if not isinstance(target, dict) or (
        leaf not in target and parts != ["delegation", "max_workers"]
    ):
        raise ValueError(f"unknown override path: {raw_path}")
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value
    target[leaf] = value


def validate_config(config: Any) -> list[str]:
    if not isinstance(config, dict):
        return ["configuration must be a JSON object"]
    errors: list[str] = []

    for field in sorted(set(config) - TOP_LEVEL_FIELDS):
        errors.append(f"unknown top-level field: {field}")

    orchestrator = config.get("orchestrator")
    if orchestrator is not None:
        errors.extend(validate_model_config(orchestrator, "orchestrator"))

    agents = config.get("agents")
    if agents is not None:
        if not isinstance(agents, dict):
            errors.append("agents must be an object")
        else:
            for role in sorted(set(agents) - set(AGENT_ROLES)):
                errors.append(f"unknown agent: {role}")
            for role, value in agents.items():
                if role in AGENT_ROLES:
                    errors.extend(validate_model_config(value, f"agents.{role}"))

    delegation = config.get("delegation")
    if delegation is not None:
        errors.extend(validate_delegation(delegation))

    return sorted(set(errors))


def validate_model_config(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors = [
        f"unknown field: {path}.{field}"
        for field in sorted(set(value) - MODEL_FIELDS)
    ]
    model = value.get("model")
    if "model" in value and (not isinstance(model, str) or not model.strip()):
        errors.append(f"{path}.model must be a non-empty string")
    effort = value.get("reasoning_effort")
    if "reasoning_effort" in value and (
        not isinstance(effort, str) or effort not in REASONING_EFFORTS
    ):
        errors.append(
            f"{path}.reasoning_effort must be one of: "
            + ", ".join(sorted(REASONING_EFFORTS))
        )
    return errors


def validate_delegation(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["delegation must be an object"]
    errors = [
        f"delegation.{field} is obsolete; {advice}"
        for field, advice in OBSOLETE_DELEGATION_FIELDS.items()
        if field in value
    ]
    errors.extend(
        f"unknown field: delegation.{field}"
        for field in sorted(set(value) - DELEGATION_FIELDS - set(OBSOLETE_DELEGATION_FIELDS))
    )
    mode = value.get("mode")
    if "mode" in value and (
        not isinstance(mode, str) or mode not in DELEGATION_MODES
    ):
        errors.append(
            "delegation.mode must be one of: "
            + ", ".join(sorted(DELEGATION_MODES))
        )
    maximum = value.get("max_workers")
    if "max_workers" in value and maximum is not None and (
        not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1
    ):
        errors.append("delegation.max_workers must be a positive integer or null")
    retries = value.get("max_retries_per_packet")
    if "max_retries_per_packet" in value and (
        not isinstance(retries, int) or isinstance(retries, bool)
    ):
        errors.append("delegation.max_retries_per_packet must be an integer")
    if (
        isinstance(retries, int)
        and not isinstance(retries, bool)
        and not 0 <= retries <= 2
    ):
        errors.append("delegation.max_retries_per_packet must be between 0 and 2")
    return errors


def spawn_settings(config: dict[str, Any], role: str) -> dict[str, str]:
    role = ROLE_ALIASES.get(role, role)
    if role == "orchestrator":
        selected = config["orchestrator"]
    elif role in AGENT_ROLES:
        selected = config["agents"][role]
    else:
        raise ValueError(f"unknown role: {role}")
    return {
        key: value
        for key, value in selected.items()
        if key in MODEL_FIELDS and value != "inherit"
    }


def emit_validation(errors: list[str]) -> int:
    if errors:
        print("LunaMaxing configuration validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LunaMaxing configuration validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
