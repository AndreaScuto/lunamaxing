#!/usr/bin/env python3
"""Validate a LunaMaxing packet or worker result expressed as JSON."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from roles import AGENT_ROLES, ROLE_ALIASES, ROLE_REGISTRY, canonical_role  # noqa: E402

ROLES = {*AGENT_ROLES, *ROLE_ALIASES}
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
STATUSES = {"DONE", "NEEDS_ORCHESTRATOR_DECISION", "BLOCKED"}
PACKET_FIELDS = (
    "role",
    "objective",
    "scope",
    "do_not_touch",
    "acceptance_criteria",
    "validation",
)
OPTIONAL_PACKET_FIELDS = (
    "model",
    "reasoning_effort",
    "context",
    "dependencies",
    "output_contract",
    "ownership",
    "read_only",
    "risk",
    "tool_budget",
    "expected_files",
    "stop_conditions",
    "id",
)
RESULT_FIELDS = (
    "status",
    "summary",
    "model_used",
    "reasoning_effort_used",
    "model_fallback",
    "files_changed",
    "tests_run",
    "evidence",
    "assumptions",
    "unresolved_risks",
)


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return emit(args, [f"unable to read JSON: {exc}"])
    if not isinstance(payload, dict):
        return emit(args, ["top-level JSON value must be an object"])

    if args.kind == "packet":
        errors = validate_packet(payload)
    elif args.kind == "result":
        errors = validate_result(payload)
    else:
        errors = validate_packet(payload) if "role" in payload else validate_result(payload)
    if args.packet is not None:
        try:
            packet = json.loads(args.packet.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to read reference packet: {exc}")
        else:
            if isinstance(packet, dict):
                errors.extend(validate_result_against_packet(payload, packet))
            else:
                errors.append("reference packet must be a JSON object")
    return emit(args, sorted(set(errors)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--kind",
        choices=("auto", "packet", "result"),
        default="auto",
        help="Payload type; auto detects from the role field.",
    )
    parser.add_argument(
        "--packet",
        type=Path,
        help="Packet JSON used to check a worker result's scope.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def emit(args: argparse.Namespace, errors: list[str]) -> int:
    result = {"ok": not errors, "errors": errors}
    if args.as_json:
        print(json.dumps(result, indent=2))
    elif errors:
        print("LunaMaxing packet validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print("LunaMaxing packet validation passed")
    return 1 if errors else 0


def validate_packet(packet: dict[str, Any]) -> list[str]:
    if not isinstance(packet, dict):
        return ["packet must be a JSON object"]
    errors = missing_fields(packet, PACKET_FIELDS)
    role = packet.get("role")
    canonical = canonical_role(role) if isinstance(role, str) else ""
    role_config = ROLE_REGISTRY.get(canonical)
    if role_config is None:
        errors.append(f"role must be one of: {', '.join(sorted(ROLES))}")
    if not isinstance(packet.get("objective"), str) or not packet["objective"].strip():
        errors.append("objective must be a non-empty string")
    if "context" in packet and (
        not isinstance(packet.get("context"), str) or not packet["context"].strip()
    ):
        errors.append("context must be a non-empty string when provided")
    for field in (
        "scope",
        "do_not_touch",
        "acceptance_criteria",
        "validation",
    ):
        if not isinstance(packet.get(field), list) or not all(
            isinstance(item, str) and item.strip() for item in packet[field]
        ):
            errors.append(f"{field} must be a list of non-empty strings")
    for field in ("dependencies", "output_contract"):
        if field in packet and (
            not isinstance(packet.get(field), list)
            or not all(isinstance(item, str) and item.strip() for item in packet[field])
        ):
            errors.append(f"{field} must be a list of non-empty strings when provided")
    if not packet.get("scope"):
        errors.append("scope must contain at least one path or symbol")
    if not packet.get("acceptance_criteria"):
        errors.append("acceptance_criteria must contain at least one criterion")
    if "output_contract" in packet and not packet.get("output_contract"):
        errors.append("output_contract must contain at least one field when provided")

    default_read_only = role_config["default_read_only"] if role_config else False
    read_only = packet.get("read_only", default_read_only)
    if not isinstance(read_only, bool):
        errors.append("read_only must be boolean when provided")
    ownership = packet.get("ownership")
    ownership_patterns = patterns(ownership)
    if ownership is not None and not valid_pattern_list(ownership):
        errors.append("ownership must contain non-empty relative path patterns when provided")
    if role_config and not role_config["may_write"] and read_only is False:
        errors.append(f"{canonical} is read-only and cannot write")
    if role_config and role_config["may_write"] and read_only is False:
        if not ownership_patterns:
            errors.append("writable packet requires non-empty ownership")
        if canonical == "tester" and any(
            not is_test_owned_pattern(item) for item in ownership_patterns
        ):
            errors.append("tester ownership must be limited to tests/** or test files")
    model = packet.get("model")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        errors.append("model must be a non-empty string when provided")
    effort = packet.get("reasoning_effort")
    if effort is not None and (
        not isinstance(effort, str) or effort not in REASONING_EFFORTS
    ):
        errors.append(
            "reasoning_effort must be one of: "
            + ", ".join(sorted(REASONING_EFFORTS))
        )
    return errors


def validate_result(result: dict[str, Any]) -> list[str]:
    if not isinstance(result, dict):
        return ["result must be a JSON object"]
    errors = missing_fields(result, RESULT_FIELDS)
    if not isinstance(result.get("status"), str) or result["status"] not in STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(STATUSES))}")
    if not isinstance(result.get("summary"), str) or not result["summary"].strip():
        errors.append("summary must be a non-empty string")
    if not isinstance(result.get("model_used"), str) or not result["model_used"].strip():
        errors.append("model_used must be a non-empty string")
    if not isinstance(result.get("reasoning_effort_used"), str) or result[
        "reasoning_effort_used"
    ] not in REASONING_EFFORTS:
        errors.append(
            "reasoning_effort_used must be one of: "
            + ", ".join(sorted(REASONING_EFFORTS))
        )
    fallback = result.get("model_fallback")
    if fallback is not None and (not isinstance(fallback, str) or not fallback.strip()):
        errors.append("model_fallback must be null or a non-empty string")
    if not isinstance(result.get("files_changed"), list) or not all(
        isinstance(item, str) and item.strip() for item in result["files_changed"]
    ):
        errors.append("files_changed must be a list of paths")
    if not isinstance(result.get("tests_run"), list):
        errors.append("tests_run must be a list")
    else:
        for index, test in enumerate(result["tests_run"]):
            if not isinstance(test, dict):
                errors.append(f"tests_run[{index}] must be an object")
                continue
            if not isinstance(test.get("command"), str) or not test["command"].strip():
                errors.append(f"tests_run[{index}].command must be non-empty")
            if not isinstance(test.get("result"), str) or test["result"] not in {
                "pass",
                "fail",
                "not-run",
            }:
                errors.append(
                    f"tests_run[{index}].result must be pass, fail, or not-run"
                )
    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be a list")
    elif result.get("status") == "DONE":
        if not evidence:
            errors.append("DONE result requires evidence")
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or not all(
                isinstance(item.get(field), str) and item[field].strip()
                for field in ("kind", "claim")
            ):
                errors.append(f"evidence[{index}] must include non-empty kind and claim")
    for field in ("assumptions", "unresolved_risks"):
        if not isinstance(result.get(field), list):
            errors.append(f"{field} must be a list")
    files = result.get("files_changed")
    if isinstance(files, list):
        for index, path in enumerate(files):
            normalized = normalize_path(path)
            if normalized is None:
                errors.append(f"files_changed[{index}] must be a relative path")
    return errors


def validate_result_against_packet(
    result: dict[str, Any], packet: dict[str, Any]
) -> list[str]:
    errors = validate_packet(packet)
    if not isinstance(result, dict):
        return errors + ["result must be a JSON object"]
    errors.extend(validate_result(result))
    if not isinstance(packet, dict):
        return errors
    files = result.get("files_changed", [])
    if not isinstance(files, list):
        return errors
    role = packet.get("role")
    canonical = canonical_role(role) if isinstance(role, str) else ""
    role_config = ROLE_REGISTRY.get(canonical, {})
    read_only = not role_config.get("may_write", True) or packet.get(
        "read_only", role_config.get("default_read_only", False)
    ) is True
    if read_only and files:
        errors.append("read-only packet result must have files_changed: []")
    scope = packet.get("scope", [])
    forbidden = packet.get("do_not_touch", [])
    ownership = patterns(packet.get("ownership"))
    for path in files:
        if not path_is_allowed(path, scope):
            errors.append(f"changed path is outside packet scope: {path}")
        if not read_only and not path_is_allowed(path, ownership):
            errors.append(f"changed path is outside packet ownership: {path}")
        if path_matches_any(path, forbidden):
            errors.append(f"changed path is forbidden by packet: {path}")
        if canonical == "tester" and not read_only and not is_test_owned_path(path):
            errors.append(f"tester changed a non-test-owned path: {path}")
    return errors


def missing_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if field not in payload]


def patterns(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def valid_pattern_list(value: Any) -> bool:
    items = [value] if isinstance(value, str) else value
    return (
        isinstance(items, list)
        and bool(items)
        and all(isinstance(item, str) and valid_path_pattern(item) for item in items)
    )


def valid_path_pattern(raw: str) -> bool:
    value = raw.replace("\\", "/").strip()
    parts = value.split("/")
    return bool(value) and not value.startswith("/") and not (
        len(value) > 1 and value[0].isalpha() and value[1] == ":"
    ) and not any(part in {"", ".", ".."} for part in parts)


def is_test_owned_pattern(pattern: str) -> bool:
    if not valid_path_pattern(pattern):
        return False
    parts = pattern.replace("\\", "/").strip().split("/")
    if any(part.casefold() in {"test", "tests", "__tests__"} for part in parts[:-1]):
        return True
    name = parts[-1].casefold()
    return (
        name.startswith(("test_", "test."))
        or name.endswith("_test")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
    )


def is_test_owned_path(path: Any) -> bool:
    normalized = normalize_path(path)
    if normalized is None:
        return False
    parts = normalized.casefold().split("/")
    return any(part in {"test", "tests", "__tests__"} for part in parts[:-1]) or (
        is_test_owned_pattern(normalized)
    )


def normalize_path(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.replace("\\", "/").strip()
    if not valid_path_pattern(value):
        return None
    path = PurePosixPath(value)
    if path.is_absolute():
        return None
    return path.as_posix()


def path_is_allowed(path: str, patterns: list[Any]) -> bool:
    normalized = normalize_path(path)
    if normalized is None:
        return False
    return path_matches_any(normalized, patterns)


def path_matches_any(path: str, pattern_values: Any) -> bool:
    normalized = normalize_path(path)
    if normalized is None:
        return False
    for raw_pattern in pattern_list(pattern_values):
        if not isinstance(raw_pattern, str):
            continue
        pattern = raw_pattern.replace("\\", "/").strip()
        if not valid_path_pattern(pattern):
            continue
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif match_path_segments(normalized, pattern):
            return True
    return False


def match_path_segments(path: str, pattern: str) -> bool:
    segments = path.split("/")
    globs = pattern.split("/")

    @lru_cache(maxsize=None)
    def matches(path_index: int, glob_index: int) -> bool:
        if glob_index == len(globs):
            return path_index == len(segments)
        if globs[glob_index] == "**":
            return matches(path_index, glob_index + 1) or (
                path_index < len(segments) and matches(path_index + 1, glob_index)
            )
        return (
            path_index < len(segments)
            and fnmatch.fnmatchcase(segments[path_index], globs[glob_index])
            and matches(path_index + 1, glob_index + 1)
        )

    return matches(0, 0)


def pattern_list(value: Any) -> list[Any]:
    return [value] if isinstance(value, str) else value if isinstance(value, list) else []


if __name__ == "__main__":
    raise SystemExit(main())
