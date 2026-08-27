#!/usr/bin/env python3
"""Dependency-free validation for the LunaMaxing skill and optional plugin wrapper."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

TODO_MARKER = "[TODO" + ":"
REQUIRED_BODY_MARKERS = (
    "Sol",
    "Luna",
    "max_workers = 5",
    "NEEDS_ORCHESTRATOR_DECISION",
    "references/protocols.md",
    "references/runtime-capabilities.md",
    "references/librarian.md",
    "references/benchmarks.md",
    "references/configuration.md",
    "references/runtime-notes.md",
    "references/evals.md",
)

REQUIRED_REFERENCES = (
    "references/protocols.md",
    "references/runtime-capabilities.md",
    "references/librarian.md",
    "references/benchmarks.md",
    "references/configuration.md",
    "references/runtime-notes.md",
    "references/evals.md",
)

REQUIRED_AGENT_KEYS = ("display_name:", "short_description:", "default_prompt:")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill_path",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Skill directory (defaults to the parent of scripts/).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit a machine-readable result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = Path(args.skill_path).expanduser().resolve()
    errors = validate_skill(skill_root)
    result: dict[str, Any] = {
        "skill_path": str(skill_root),
        "ok": not errors,
        "errors": errors,
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    elif errors:
        print("LunaMaxing validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"LunaMaxing validation passed: {skill_root}")
    return 1 if errors else 0


def validate_skill(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill_path = skill_root / "SKILL.md"
    if not skill_path.is_file():
        return [f"missing {skill_path}"]

    try:
        contents = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unable to read {skill_path}: {exc}"]

    frontmatter, body = split_frontmatter(contents, errors)
    if frontmatter is not None:
        name = frontmatter.get("name", "").strip()
        description = frontmatter.get("description", "").strip()
        if name != skill_root.name:
            errors.append(
                f"frontmatter name must be {skill_root.name!r}, got {name!r}"
            )
        if not description:
            errors.append("frontmatter description must be non-empty")

    if TODO_MARKER in contents:
        errors.append(f"{skill_path} contains a scaffold placeholder")
    for marker in REQUIRED_BODY_MARKERS:
        if marker not in body:
            errors.append(f"SKILL.md is missing required marker: {marker}")

    for relative in REQUIRED_REFERENCES:
        if not (skill_root / relative).is_file():
            errors.append(f"missing reference: {relative}")

    agent_path = skill_root / "agents" / "openai.yaml"
    if not agent_path.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        try:
            agent_text = agent_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"unable to read agents/openai.yaml: {exc}")
        else:
            if TODO_MARKER in agent_text:
                errors.append("agents/openai.yaml contains a scaffold placeholder")
            for key in REQUIRED_AGENT_KEYS:
                if key not in agent_text:
                    errors.append(f"agents/openai.yaml is missing {key}")

    for path in skill_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml", ".json"}:
            continue
        try:
            if TODO_MARKER in path.read_text(encoding="utf-8"):
                errors.append(f"{path.relative_to(skill_root)} contains a scaffold placeholder")
        except OSError as exc:
            errors.append(f"unable to inspect {path}: {exc}")

    validate_plugin_wrapper(skill_root, errors)
    return sorted(set(errors))


def split_frontmatter(
    contents: str, errors: list[str]
) -> tuple[dict[str, str] | None, str]:
    lines = contents.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append("SKILL.md must start with YAML frontmatter")
        return None, contents
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        errors.append("SKILL.md frontmatter is not closed")
        return None, contents

    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            errors.append(f"unsupported frontmatter line: {line}")
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[match.group(1)] = value
    return values, "\n".join(lines[end + 1 :])


def validate_plugin_wrapper(skill_root: Path, errors: list[str]) -> None:
    plugin_root = skill_root.parent.parent
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plugin manifest: {exc}")
        return
    if not isinstance(manifest, dict):
        errors.append("plugin manifest must be a JSON object")
        return
    if manifest.get("name") != "lunamaxing":
        errors.append("plugin manifest name must be lunamaxing")
    if not isinstance(manifest.get("version"), str) or not SEMVER_RE.fullmatch(
        manifest["version"]
    ):
        errors.append("plugin manifest version must be semantic versioning")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin manifest skills must resolve to ./skills/")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin manifest interface must be an object")
        return
    if interface.get("displayName") != "LunaMaxing":
        errors.append("plugin manifest displayName must be LunaMaxing")
    for field in ("composerIcon", "logo"):
        validate_asset_path(plugin_root, interface.get(field), f"interface.{field}", errors)


def validate_asset_path(
    plugin_root: Path, raw_path: Any, field: str, errors: list[str]
) -> None:
    if not isinstance(raw_path, str) or not raw_path.startswith("./"):
        errors.append(f"{field} must be a relative ./ path")
        return
    candidate = PurePosixPath(raw_path[2:])
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        errors.append(f"{field} must remain inside the plugin")
        return
    resolved = (plugin_root / candidate.as_posix()).resolve()
    if not resolved.is_relative_to(plugin_root.resolve()):
        errors.append(f"{field} escapes the plugin root")
    elif not resolved.is_file():
        errors.append(f"{field} points to a missing file: {raw_path}")


if __name__ == "__main__":
    raise SystemExit(main())
