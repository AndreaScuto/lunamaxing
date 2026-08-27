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


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return emit(args, [f"unable to read JSON: {exc}"])
    packets = payload.get("wave") if isinstance(payload, dict) else payload
    errors = validate_wave(packets, args.max_workers)
    return emit(args, errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--max-workers", type=int, default=5)
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


def validate_wave(packets: Any, max_workers: int = 5) -> list[str]:
    if not isinstance(packets, list):
        return ["wave must be a JSON array"]
    errors: list[str] = []
    if max_workers < 0:
        errors.append("max_workers must be non-negative")
    if len(packets) > max_workers:
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

    for index, packet in enumerate(packets):
        if not isinstance(packet, dict):
            continue
        for dependency in packet.get("dependencies", []):
            if dependency in ids:
                errors.append(
                    f"wave[{index}] depends on {dependency}; move it to a later wave"
                )

    writers: list[tuple[int, dict[str, Any], list[str]]] = []
    for index, packet in enumerate(packets):
        if not isinstance(packet, dict) or packet.get("read_only") is True:
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
    left = left.rstrip("/")
    right = right.rstrip("/")
    if left == right:
        return True
    left_base = left[:-3].rstrip("/") if left.endswith("/**") else left
    right_base = right[:-3].rstrip("/") if right.endswith("/**") else right
    if left.endswith("/**") or right.endswith("/**"):
        return (
            left_base == right_base
            or left_base.startswith(right_base + "/")
            or right_base.startswith(left_base + "/")
        )
    if fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    left_literal = left.split("*", 1)[0].split("?", 1)[0].rstrip("/")
    right_literal = right.split("*", 1)[0].split("?", 1)[0].rstrip("/")
    return bool(left_literal and right_literal and (
        left_literal.startswith(right_literal + "/")
        or right_literal.startswith(left_literal + "/")
    ))


if __name__ == "__main__":
    raise SystemExit(main())
