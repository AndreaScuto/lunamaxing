"""Checks for optional native Codex agent generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_agents.py"


class NativeAgentGenerationTests(unittest.TestCase):
    def run_generator(self, project: Path, *flags: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(project), *flags],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_preview_and_safe_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".lunamaxing.json").write_text(
                json.dumps({"agents": {"oracle": {"model": "gpt-6-astra", "reasoning_effort": "high"}}}),
                encoding="utf-8",
            )
            preview = self.run_generator(project, "--dry-run")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertFalse((project / ".codex").exists())

            result = self.run_generator(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            files = sorted((project / ".codex" / "agents").glob("*.toml"))
            self.assertEqual(len(files), 7)
            generated = {file.name: file.read_bytes() for file in files}
            agents = {file.stem: tomllib.loads(file.read_text(encoding="utf-8")) for file in files}
            self.assertEqual(agents["oracle"]["model"], "gpt-6-astra")
            self.assertEqual(agents["oracle"]["model_reasoning_effort"], "high")
            for role in ("oracle", "explorer", "librarian", "reviewer"):
                self.assertEqual(agents[role]["sandbox_mode"], "read-only")
            for role in ("designer", "fixer", "tester"):
                self.assertNotIn("sandbox_mode", agents[role])
            for agent in agents.values():
                self.assertTrue(all(agent.get(key) for key in ("name", "description", "developer_instructions")))

            oracle_file = project / ".codex" / "agents" / "oracle.toml"
            oracle_file.write_text("name = 'personal'\n", encoding="utf-8")
            blocked = self.run_generator(project)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(oracle_file.read_text(encoding="utf-8"), "name = 'personal'\n")
            forced = self.run_generator(project, "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertEqual(tomllib.loads(oracle_file.read_text(encoding="utf-8"))["name"], "oracle")
            self.assertEqual(
                generated,
                {
                    file.name: file.read_bytes()
                    for file in (project / ".codex" / "agents").glob("*.toml")
                },
            )


if __name__ == "__main__":
    unittest.main()
