#!/usr/bin/env python3
"""Validate a LunaMaxing packet or worker result expressed as JSON."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROLES = {
    "designer",
    "explorer",
    "fixer",
    "librarian",
    "oracle",
    "researcher",
    "reviewer",
    "tester",
}
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
    "model",
    "reasoning_effort",
    "objective",
    "scope",
    "do_not_touch",
    "context",
    "acceptance_criteria",
    "validation",
    "dependencies",
    "output_contract",
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
    errors = missing_fields(packet, PACKET_FIELDS)
    role = packet.get("role")
    if role not in ROLES:
        errors.append(f"role must be one of: {', '.join(sorted(ROLES))}")
    for field in ("objective", "context"):
        if not isinstance(packet.get(field), str) or not packet[field].strip():
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "scope",
        "do_not_touch",
        "acceptance_criteria",
        "validation",
        "dependencies",
        "output_contract",
    ):
        if not isinstance(packet.get(field), list) or not all(
            isinstance(item, str) and item.strip() for item in packet[field]
        ):
            errors.append(f"{field} must be a list of non-empty strings")
    if not packet.get("scope"):
        errors.append("scope must contain at least one path or symbol")
    if not packet.get("acceptance_criteria"):
        errors.append("acceptance_criteria must contain at least one criterion")
    if not packet.get("output_contract"):
        errors.append("output_contract must contain at least one field")
    elif isinstance(packet.get("output_contract"), list):
        for field in RESULT_FIELDS:
            if field not in packet["output_contract"]:
                errors.append(f"output_contract missing required field: {field}")

    read_only = packet.get("read_only", False)
    if not isinstance(read_only, bool):
        errors.append("read_only must be boolean when provided")
    if read_only is False and not isinstance(packet.get("ownership"), str):
        errors.append("write-capable packets require an ownership string")
    if isinstance(packet.get("ownership"), str) and not packet["ownership"].strip():
        errors.append("ownership must be non-empty when provided")
    model = packet.get("model")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        errors.append("model must be a non-empty string when provided")
    effort = packet.get("reasoning_effort")
    if effort is not None and effort not in REASONING_EFFORTS:
        errors.append(
            "reasoning_effort must be one of: "
            + ", ".join(sorted(REASONING_EFFORTS))
        )
    return errors


def validate_result(result: dict[str, Any]) -> list[str]:
    errors = missing_fields(result, RESULT_FIELDS)
    if result.get("status") not in STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(STATUSES))}")
    if not isinstance(result.get("summary"), str) or not result["summary"].strip():
        errors.append("summary must be a non-empty string")
    if not isinstance(result.get("model_used"), str) or not result["model_used"].strip():
        errors.append("model_used must be a non-empty string")
    if result.get("reasoning_effort_used") not in REASONING_EFFORTS:
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
            if test.get("result") not in {"pass", "fail", "not-run"}:
                errors.append(
                    f"tests_run[{index}].result must be pass, fail, or not-run"
                )
    for field in ("evidence", "assumptions", "unresolved_risks"):
        if not isinstance(result.get(field), list):
            errors.append(f"{field} must be a list")
    for index, path in enumerate(result.get("files_changed", [])):
        normalized = normalize_path(path)
        if normalized is None:
            errors.append(f"files_changed[{index}] must be a relative path")
    return errors


def validate_result_against_packet(
    result: dict[str, Any], packet: dict[str, Any]
) -> list[str]:
    errors = []
    errors.extend(validate_packet(packet))
    errors.extend(validate_result(result))
    if not isinstance(result, dict):
        return errors
    files = result.get("files_changed", [])
    if packet.get("read_only") is True and files:
        errors.append("read-only packet result must have files_changed: []")
    scope = packet.get("scope", [])
    forbidden = packet.get("do_not_touch", [])
    for path in files:
        if not path_is_allowed(path, scope):
            errors.append(f"changed path is outside packet scope: {path}")
        if path_matches_any(path, forbidden):
            errors.append(f"changed path is forbidden by packet: {path}")
    return errors


def missing_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if field not in payload]


def normalize_path(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.replace("\\", "/").strip()
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def path_is_allowed(path: str, patterns: list[Any]) -> bool:
    normalized = normalize_path(path)
    if normalized is None:
        return False
    return path_matches_any(normalized, patterns)


def path_matches_any(path: str, patterns: list[Any]) -> bool:
    normalized = normalize_path(path)
    if normalized is None:
        return False
    for raw_pattern in patterns:
        if not isinstance(raw_pattern, str):
            continue
        pattern = raw_pattern.replace("\\", "/").strip()
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif fnmatch.fnmatchcase(normalized, pattern):
            return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
