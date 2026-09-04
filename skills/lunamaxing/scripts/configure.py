#!/usr/bin/env python3
"""Create, validate, and resolve LunaMaxing model-routing configuration."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SKILL_ROOT / "assets" / "lunamaxing.example.json"
AGENT_ROLES = (
    "oracle",
    "explorer",
    "librarian",
    "designer",
    "fixer",
    "tester",
    "reviewer",
)
ROLE_ALIASES = {"researcher": "librarian"}
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
    "min_workers_nontrivial",
    "target_workers_complex",
    "max_retries_per_packet",
    "decompose_before_local",
}


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            return init_config(args.path)
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
    if not isinstance(target, dict) or leaf not in target:
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

    effective = deep_merge(default_config(), config)
    values = effective.get("delegation")
    if isinstance(values, dict):
        minimum = values.get("min_workers_nontrivial")
        target = values.get("target_workers_complex")
        maximum = values.get("max_workers")
    else:
        minimum = target = maximum = None
    if all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in (minimum, target, maximum)
    ):
        if minimum > maximum:
            errors.append("delegation.min_workers_nontrivial cannot exceed max_workers")
        if target > maximum:
            errors.append("delegation.target_workers_complex cannot exceed max_workers")
        if target < minimum:
            errors.append(
                "delegation.target_workers_complex cannot be below min_workers_nontrivial"
            )
    return sorted(set(errors))


def validate_model_config(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors = [
        f"unknown field: {path}.{field}"
        for field in sorted(set(value) - MODEL_FIELDS)
    ]
    model = value.get("model")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        errors.append(f"{path}.model must be a non-empty string")
    effort = value.get("reasoning_effort")
    if effort is not None and effort not in REASONING_EFFORTS:
        errors.append(
            f"{path}.reasoning_effort must be one of: "
            + ", ".join(sorted(REASONING_EFFORTS))
        )
    return errors


def validate_delegation(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["delegation must be an object"]
    errors = [
        f"unknown field: delegation.{field}"
        for field in sorted(set(value) - DELEGATION_FIELDS)
    ]
    mode = value.get("mode")
    if mode is not None and mode not in DELEGATION_MODES:
        errors.append(
            "delegation.mode must be one of: "
            + ", ".join(sorted(DELEGATION_MODES))
        )
    for field in (
        "max_workers",
        "min_workers_nontrivial",
        "target_workers_complex",
        "max_retries_per_packet",
    ):
        number = value.get(field)
        if number is not None and (
            not isinstance(number, int) or isinstance(number, bool)
        ):
            errors.append(f"delegation.{field} must be an integer")
    maximum = value.get("max_workers")
    if (
        isinstance(maximum, int)
        and not isinstance(maximum, bool)
        and not 1 <= maximum <= 5
    ):
        errors.append("delegation.max_workers must be between 1 and 5")
    for field in ("min_workers_nontrivial", "target_workers_complex"):
        number = value.get(field)
        if isinstance(number, int) and not isinstance(number, bool) and not 0 <= number <= 5:
            errors.append(f"delegation.{field} must be between 0 and 5")
    retries = value.get("max_retries_per_packet")
    if isinstance(retries, int) and not isinstance(retries, bool) and not 0 <= retries <= 2:
        errors.append("delegation.max_retries_per_packet must be between 0 and 2")
    decompose = value.get("decompose_before_local")
    if decompose is not None and not isinstance(decompose, bool):
        errors.append("delegation.decompose_before_local must be boolean")
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
