#!/usr/bin/env python3
"""Validate a ready LunaMaxing wave and detect writer ownership conflicts."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_packet import validate_packet  # noqa: E402
from roles import ROLE_REGISTRY, canonical_role  # noqa: E402


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return emit(args, [f"unable to read JSON: {exc}"])
    packets = payload.get("wave") if isinstance(payload, dict) else payload
    completed_ids = payload.get("completed_ids") if isinstance(payload, dict) else None
    errors = validate_wave(packets, args.max_workers, completed_ids)
    return emit(args, errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--max-workers", type=int, help="Optional worker ceiling for this wave.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def emit(args: argparse.Namespace, errors: list[str]) -> int:
    result = {"ok": not errors, "errors": sorted(set(errors))}
    if args.as_json:
        print(json.dumps(result, indent=2))
    elif errors:
        print("LunaMaxing wave validation failed:")
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("LunaMaxing wave validation passed")
    return 1 if errors else 0


def validate_wave(
    packets: Any, max_workers: int | None = None, completed_ids: Any = None
) -> list[str]:
    """Validate one wave; unknown external dependencies need completed_ids context."""
    if not isinstance(packets, list):
        return ["wave must be a JSON array"]
    errors: list[str] = []
    if completed_ids is not None and (
        not isinstance(completed_ids, list)
        or not all(isinstance(item, str) and item.strip() for item in completed_ids)
    ):
        errors.append("completed_ids must be a list of non-empty packet IDs")
        completed_ids = None
    if max_workers is not None:
        if max_workers < 0:
            errors.append("max_workers must be non-negative")
        elif len(packets) > max_workers:
            errors.append(f"wave contains {len(packets)} packets; ceiling is {max_workers}")

    ids: set[str] = set()
    for index, packet in enumerate(packets):
        if not isinstance(packet, dict):
            errors.append(f"wave[{index}] must be an object")
            continue
        errors.extend(
            f"wave[{index}]: {error}" for error in validate_packet(packet)
        )
        packet_id = packet.get("id")
        if packet_id is not None:
            if not isinstance(packet_id, str) or not packet_id.strip():
                errors.append(f"wave[{index}].id must be a non-empty string")
            elif packet_id in ids:
                errors.append(f"duplicate packet id: {packet_id}")
            else:
                ids.add(packet_id)

    completed = set(completed_ids or [])
    if len(completed) != len(completed_ids or []):
        errors.append("completed_ids must not contain duplicates")
    for packet_id in completed & ids:
        errors.append(f"packet id is both completed and in this wave: {packet_id}")

    for index, packet in enumerate(packets):
        if not isinstance(packet, dict):
            continue
        dependencies = packet.get("dependencies", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if not isinstance(dependency, str) or not dependency.strip():
                continue
            if dependency in ids:
                errors.append(
                    f"wave[{index}] depends on {dependency}; move it to a later wave"
                )
            elif completed_ids is not None and dependency not in completed:
                errors.append(f"wave[{index}] has unknown dependency: {dependency}")

    writers: list[tuple[int, dict[str, Any], list[str]]] = []
    for index, packet in enumerate(packets):
        if not isinstance(packet, dict):
            continue
        role = ROLE_REGISTRY.get(canonical_role(packet.get("role", "")), {})
        if not role or not role.get("may_write") or packet.get(
            "read_only", role.get("default_read_only", False)
        ) is True:
            continue
        patterns = ownership_patterns(packet.get("ownership"))
        if not patterns:
            continue
        writers.append((index, packet, patterns))
    for left_index, left, left_patterns in writers:
        for right_index, right, right_patterns in writers:
            if left_index >= right_index:
                continue
            for left_pattern in left_patterns:
                for right_pattern in right_patterns:
                    if patterns_overlap(left_pattern, right_pattern):
                        errors.append(
                            "write ownership conflict between "
                            f"wave[{left_index}] ({left_pattern}) and "
                            f"wave[{right_index}] ({right_pattern})"
                        )
    return sorted(set(errors))


def ownership_patterns(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.replace("\\", "/").strip()] if value.strip() else []
    if isinstance(value, list):
        return [
            item.replace("\\", "/").strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]
    return []


def patterns_overlap(left: str, right: str) -> bool:
    left_parts = left.replace("\\", "/").strip("/").split("/")
    right_parts = right.replace("\\", "/").strip("/").split("/")
    pending = [(0, 0)]
    seen = set()
    while pending:
        left_index, right_index = pending.pop()
        state = (left_index, right_index)
        if state in seen:
            continue
        seen.add(state)
        if left_index == len(left_parts) and right_index == len(right_parts):
            return True
        left_part = left_parts[left_index] if left_index < len(left_parts) else None
        right_part = right_parts[right_index] if right_index < len(right_parts) else None
        if left_part == "**":
            pending.append((left_index + 1, right_index))
            if right_part is not None and right_part != "**":
                pending.append((left_index, right_index + 1))
        if right_part == "**":
            pending.append((left_index, right_index + 1))
            if left_part is not None and left_part != "**":
                pending.append((left_index + 1, right_index))
        if (
            left_part is not None
            and right_part is not None
            and left_part != "**"
            and right_part != "**"
        ):
            if segment_patterns_overlap(left_part, right_part):
                pending.append((left_index + 1, right_index + 1))
    return compatible_prefix(left_parts, right_parts) or compatible_prefix(
        right_parts, left_parts
    )


def compatible_prefix(prefix: list[str], path: list[str]) -> bool:
    return len(prefix) < len(path) and all(
        segment_patterns_overlap(left, right)
        for left, right in zip(prefix, path)
    )


def segment_patterns_overlap(left: str, right: str) -> bool:
    if left == right:
        return True
    left_has_glob = any(char in left for char in "*?[")
    right_has_glob = any(char in right for char in "*?[")
    if not left_has_glob:
        return fnmatch.fnmatchcase(left, right)
    if not right_has_glob:
        return fnmatch.fnmatchcase(right, left)
    # ponytail: ambiguous glob pairs conflict conservatively; use literal paths
    # if that over-serializes.
    return True


if __name__ == "__main__":
    raise SystemExit(main())
