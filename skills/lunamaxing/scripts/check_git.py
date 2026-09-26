#!/usr/bin/env python3
"""Check a packet against actual uncommitted Git paths in a clean baseline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_packet import path_is_allowed, path_matches_any, validate_packet  # noqa: E402
from roles import ROLE_REGISTRY, canonical_role  # noqa: E402


def changed_paths(root: Path) -> list[str]:
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if Path(top).resolve() != root.resolve():
            raise RuntimeError("verification unavailable: path is not the repository root")
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all", "--no-renames", "-z"],
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"verification unavailable: {exc}") from exc
    return sorted({entry[3:] for entry in result.stdout.decode("utf-8", "surrogateescape").split("\0") if entry})


def check_paths(paths: list[str], packet: dict) -> list[str]:
    role = ROLE_REGISTRY.get(canonical_role(packet.get("role", "")), {})
    read_only = not role.get("may_write", True) or packet.get("read_only", role.get("default_read_only", False))
    if read_only and paths:
        return ["read-only packet changed repository files"]
    ownership = packet.get("ownership", [])
    if isinstance(ownership, str):
        ownership = [ownership]
    errors = []
    for path in paths:
        if not path_is_allowed(path, packet.get("scope", [])):
            errors.append(f"outside scope: {path}")
        if not path_is_allowed(path, ownership):
            errors.append(f"outside ownership: {path}")
        if path_matches_any(path, packet.get("do_not_touch", [])):
            errors.append(f"forbidden path: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        if not isinstance(packet, dict):
            raise ValueError("packet must be a JSON object")
        paths = changed_paths(args.repo)
        errors = validate_packet(packet) + check_paths(paths, packet)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"verification unavailable: {exc}")
        return 2
    print(json.dumps({"ok": not errors, "changed_paths": paths, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
