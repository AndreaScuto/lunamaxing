"""Checks that verification inspects actual repository changes."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_git.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_git", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GitStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"], check=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("original\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "initial"], check=True)
        self.packet = {
            "role": "fixer",
            "read_only": False,
            "scope": ["src/**"],
            "ownership": "src/**",
            "do_not_touch": ["src/private/**"],
        }

    def test_actual_changed_and_untracked_paths_are_checked(self):
        checker = load_checker()
        (self.root / "src" / "main.py").write_text("changed\n", encoding="utf-8")
        (self.root / "src" / "private").mkdir()
        (self.root / "src" / "private" / "secret.py").write_text("new\n", encoding="utf-8")
        changed = checker.changed_paths(self.root)
        self.assertEqual(changed, ["src/main.py", "src/private/secret.py"])
        self.assertTrue(any("forbidden" in item for item in checker.check_paths(changed, self.packet)))

    def test_read_only_and_missing_repository(self):
        checker = load_checker()
        (self.root / "src" / "main.py").write_text("changed\n", encoding="utf-8")
        self.assertTrue(checker.check_paths(checker.changed_paths(self.root), {**self.packet, "read_only": True}))
        self.assertTrue(checker.check_paths(checker.changed_paths(self.root), {**self.packet, "role": "oracle"}))
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaisesRegex(RuntimeError, "verification unavailable"):
                checker.changed_paths(Path(other))


if __name__ == "__main__":
    unittest.main()
