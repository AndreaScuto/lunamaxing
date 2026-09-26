#!/usr/bin/env python3
"""Generate project-local Codex agent definitions from LunaMaxing config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from configure import load_json, resolve_config, spawn_settings
from roles import AGENT_ROLES, ROLE_REGISTRY


def render_agent(role: str, config: dict) -> str:
    metadata = ROLE_REGISTRY[role]
    fields = {
        "name": role,
        "description": metadata["description"],
        "developer_instructions": metadata["developer_instructions"],
    }
    settings = spawn_settings(config, role)
    if "model" in settings:
        fields["model"] = settings["model"]
    if "reasoning_effort" in settings:
        fields["model_reasoning_effort"] = settings["reasoning_effort"]
    if metadata["default_read_only"] and role != "tester":
        fields["sandbox_mode"] = "read-only"
    return "".join(
        f"{key} = {json.dumps(value, ensure_ascii=False)}\n"
        for key, value in fields.items()
    )


def generate_agents(
    project_root: Path, *, force: bool = False, dry_run: bool = False
) -> int:
    config_path = project_root / ".lunamaxing.json"
    source = load_json(config_path) if config_path.exists() else {}
    config = resolve_config(source)
    output_dir = project_root / ".codex" / "agents"
    targets = {role: output_dir / f"{role}.toml" for role in AGENT_ROLES}
    contents = {role: render_agent(role, config) for role in AGENT_ROLES}

    existing = [path for path in targets.values() if path.exists()]
    if existing and not force:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            f"refusing to overwrite existing agent file(s): {names}; use --force"
        )

    for role, path in targets.items():
        action = "Would write" if dry_run else "Writing"
        print(f"{action} {path}")
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        for role, path in targets.items():
            with path.open(
                "w" if force else "x", encoding="utf-8", newline="\n"
            ) as agent_file:
                agent_file.write(contents[role])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument(
        "--force", action="store_true", help="replace existing agent files"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show planned files without writing"
    )
    args = parser.parse_args()
    try:
        return generate_agents(args.project_root, force=args.force, dry_run=args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"LunaMaxing agent generation error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
