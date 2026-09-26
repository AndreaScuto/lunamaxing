"""Behavioral tests for LunaMaxing model routing and delegation config."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_SCRIPT = ROOT / "scripts" / "configure.py"


def load_config_module():
    spec = importlib.util.spec_from_file_location("lunamax_configure", CONFIG_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CONFIG_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.configure = load_config_module()

    def test_luna_heavy_defaults(self) -> None:
        resolved = self.configure.resolve_config({})
        self.assertEqual(resolved["orchestrator"]["model"], "inherit")
        self.assertEqual(resolved["agents"]["oracle"]["model"], "gpt-5.6-terra")
        self.assertEqual(resolved["agents"]["oracle"]["reasoning_effort"], "max")
        for role in ("explorer", "librarian", "designer", "fixer", "tester", "reviewer"):
            self.assertEqual(resolved["agents"][role]["model"], "inherit")
            self.assertEqual(resolved["agents"][role]["reasoning_effort"], "inherit")
        self.assertEqual(resolved["delegation"]["mode"], "balanced")
        self.assertNotIn("max_workers", resolved["delegation"])

    def test_project_config_overrides_one_role_without_erasing_defaults(self) -> None:
        resolved = self.configure.resolve_config(
            {
                "orchestrator": {
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                },
                "agents": {
                    "oracle": {
                        "model": "gpt-5.6-terra",
                        "reasoning_effort": "high",
                    },
                    "fixer": {"model": "gpt-5.6-sol"},
                },
            }
        )
        self.assertEqual(resolved["orchestrator"]["model"], "gpt-5.6-sol")
        self.assertEqual(resolved["agents"]["fixer"]["model"], "gpt-5.6-sol")
        self.assertEqual(resolved["agents"]["fixer"]["reasoning_effort"], "inherit")
        self.assertEqual(resolved["agents"]["designer"]["model"], "inherit")

    def test_inline_override_has_highest_precedence(self) -> None:
        resolved = self.configure.resolve_config(
            {"agents": {"oracle": {"model": "gpt-5.6-terra"}}},
            ["agents.oracle.model=gpt-5.6-sol"],
        )
        self.assertEqual(resolved["agents"]["oracle"]["model"], "gpt-5.6-sol")

    def test_invalid_config_is_rejected(self) -> None:
        errors = self.configure.validate_config(
            {
                "agents": {"unknown": {"model": "gpt-5.6-luna"}},
                "delegation": {
                    "min_workers_nontrivial": 2,
                },
            }
        )
        self.assertTrue(any("unknown agent" in error for error in errors))
        self.assertTrue(any("min_workers_nontrivial" in error for error in errors))

    def test_unhashable_enum_values_are_reported_as_invalid(self) -> None:
        errors = self.configure.validate_config(
            {
                "agents": {"oracle": {"reasoning_effort": []}},
                "delegation": {"mode": []},
            }
        )
        self.assertTrue(any("reasoning_effort must be one of" in error for error in errors))
        self.assertTrue(any("delegation.mode must be one of" in error for error in errors))

    def test_zero_worker_ceiling_is_rejected(self) -> None:
        errors = self.configure.validate_config(
            {"delegation": {"max_workers": 0}}
        )
        self.assertIn("delegation.max_workers must be a positive integer or null", errors)

    def test_explicit_ceiling_above_five_and_null_are_valid(self) -> None:
        for ceiling in (12, None):
            with self.subTest(ceiling=ceiling):
                resolved = self.configure.resolve_config({"delegation": {"max_workers": ceiling}})
                self.assertEqual(resolved["delegation"]["max_workers"], ceiling)

    def test_optional_ceiling_can_be_set_by_inline_override(self) -> None:
        resolved = self.configure.resolve_config({}, ["delegation.max_workers=12"])
        self.assertEqual(resolved["delegation"]["max_workers"], 12)

    def test_obsolete_fields_have_migration_message(self) -> None:
        for field, value in (
            ("min_workers_nontrivial", 1),
            ("target_workers_complex", 2),
            ("decompose_before_local", True),
        ):
            with self.subTest(field=field):
                errors = self.configure.validate_config({"delegation": {field: value}})
                message = next(error for error in errors if field in error)
                self.assertIn("obsolete", message)
                self.assertIn("remove it", message)
                with self.assertRaisesRegex(ValueError, "obsolete"):
                    self.configure.resolve_config({"delegation": {field: value}})

    def test_spawn_settings_are_explicit_for_workers(self) -> None:
        resolved = self.configure.resolve_config({})
        self.assertEqual(
            self.configure.spawn_settings(resolved, "oracle"),
            {"model": "gpt-5.6-terra", "reasoning_effort": "max"},
        )

    def test_legacy_researcher_routes_to_librarian(self) -> None:
        resolved = self.configure.resolve_config({})
        self.assertEqual(
            self.configure.spawn_settings(resolved, "researcher"),
            self.configure.spawn_settings(resolved, "librarian"),
        )

    def test_schema_leaves_role_names_to_canonical_registry(self) -> None:
        schema = json.loads(
            (ROOT / "assets" / "lunamaxing.schema.json").read_text(encoding="utf-8")
        )
        agents = schema["properties"]["agents"]
        self.assertNotIn("properties", agents)
        self.assertEqual(
            agents["additionalProperties"], {"$ref": "#/$defs/modelConfig"}
        )
        self.assertIn("configure.py validates role names", agents["description"])
        max_workers = schema["properties"]["delegation"]["properties"]["max_workers"]
        self.assertEqual(max_workers["type"], ["integer", "null"])
        self.assertNotIn("maximum", max_workers)


class InteractiveConfigTests(unittest.TestCase):
    def run_wizard(self, path: Path, answers: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CONFIG_SCRIPT), "interactive", str(path)],
            input="\n".join(answers) + "\n",
            text=True,
            capture_output=True,
            check=False,
        )

    def test_creates_valid_config_with_custom_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".lunamaxing.json"
            answers = ["custom-model-id", "high"] + [""] * 14
            result = self.run_wizard(path, answers)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(config["orchestrator"], {"model": "custom-model-id", "reasoning_effort": "high"})
            self.assertEqual(config["agents"]["oracle"]["model"], "gpt-5.6-terra")
            self.assertEqual(load_config_module().validate_config(config), [])

    def test_edits_existing_file_and_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".lunamaxing.json"
            original = {"agents": {"fixer": {"model": "vendor/model", "reasoning_effort": "low"}}}
            path.write_text(json.dumps(original), encoding="utf-8")
            answers = [""] * 10 + ["inherit", "max"] + [""] * 4 + ["n"]
            result = self.run_wizard(path, answers)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)
            answers[-1] = "y"
            result = self.run_wizard(path, answers)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(config["agents"]["fixer"], {"model": "inherit", "reasoning_effort": "max"})

    def test_invalid_effort_reprompts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".lunamaxing.json"
            answers = ["", "invalid-effort", "ultra"] + [""] * 14
            result = self.run_wizard(path, answers)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Invalid reasoning effort", result.stdout)
            config = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(config["orchestrator"]["reasoning_effort"], "ultra")

    def test_obsolete_fields_are_migrated_only_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".lunamaxing.json"
            original = {
                "agents": {"fixer": {"model": "vendor/model", "reasoning_effort": "low"}},
                "delegation": {
                    "mode": "eager",
                    "max_retries_per_packet": 0,
                    "min_workers_nontrivial": 1,
                    "target_workers_complex": 2,
                    "decompose_before_local": True,
                },
            }
            path.write_text(json.dumps(original), encoding="utf-8")
            answers = [""] * 16 + ["n"]
            result = self.run_wizard(path, answers)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Obsolete delegation.min_workers_nontrivial", result.stdout)
            self.assertIn("Obsolete delegation.target_workers_complex", result.stdout)
            self.assertIn("Obsolete delegation.decompose_before_local", result.stdout)
            self.assertIn("removed only if you confirm", result.stdout)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)

            answers[-1] = "y"
            result = self.run_wizard(path, answers)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(config["agents"]["fixer"], original["agents"]["fixer"])
            self.assertEqual(config["delegation"]["mode"], "eager")
            self.assertEqual(config["delegation"]["max_retries_per_packet"], 0)
            for field in (
                "min_workers_nontrivial",
                "target_workers_complex",
                "decompose_before_local",
            ):
                self.assertNotIn(field, config["delegation"])


class SkillPromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_decomposition_is_mandatory_without_worker_quotas(self) -> None:
        self.assertIn("## Mandatory decomposition pass", self.skill)
        self.assertIn("no-delegation reason", self.skill)
        self.assertIn("There is no LunaMaxing default", self.skill)
        self.assertNotIn("min_workers_nontrivial", self.skill)

    def test_role_model_routing_is_part_of_every_worker_packet(self) -> None:
        self.assertIn(".lunamaxing.json", self.skill)
        self.assertIn("model:", self.skill)
        self.assertIn("reasoning_effort:", self.skill)
        self.assertIn("**Oracle**", self.skill)
        self.assertIn("**Explorer**", self.skill)


if __name__ == "__main__":
    unittest.main()
