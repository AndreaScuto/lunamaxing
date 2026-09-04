"""Behavioral tests for LunaMaxing model routing and delegation config."""

from __future__ import annotations

import importlib.util
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
        for role in ("explorer", "librarian", "designer", "fixer", "tester", "reviewer"):
            self.assertEqual(resolved["agents"][role]["model"], "gpt-5.6-luna")
            self.assertEqual(resolved["agents"][role]["reasoning_effort"], "max")
        self.assertEqual(resolved["delegation"]["mode"], "eager")
        self.assertEqual(resolved["delegation"]["min_workers_nontrivial"], 1)

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
        self.assertEqual(resolved["agents"]["fixer"]["reasoning_effort"], "max")
        self.assertEqual(resolved["agents"]["designer"]["model"], "gpt-5.6-luna")

    def test_inline_override_has_highest_precedence(self) -> None:
        resolved = self.configure.resolve_config(
            {"agents": {"oracle": {"model": "gpt-5.6-terra"}}},
            ["agents.oracle.model=gpt-5.6-sol", "delegation.max_workers=3"],
        )
        self.assertEqual(resolved["agents"]["oracle"]["model"], "gpt-5.6-sol")
        self.assertEqual(resolved["delegation"]["max_workers"], 3)

    def test_invalid_config_is_rejected(self) -> None:
        errors = self.configure.validate_config(
            {
                "agents": {"unknown": {"model": "gpt-5.6-luna"}},
                "delegation": {
                    "max_workers": 1,
                    "min_workers_nontrivial": 2,
                },
            }
        )
        self.assertTrue(any("unknown agent" in error for error in errors))
        self.assertTrue(any("min_workers_nontrivial" in error for error in errors))

    def test_zero_worker_ceiling_is_rejected(self) -> None:
        errors = self.configure.validate_config(
            {"delegation": {"max_workers": 0}}
        )
        self.assertIn("delegation.max_workers must be between 1 and 5", errors)

    def test_spawn_settings_are_explicit_for_workers(self) -> None:
        resolved = self.configure.resolve_config({})
        self.assertEqual(
            self.configure.spawn_settings(resolved, "oracle"),
            {"model": "gpt-5.6-terra", "reasoning_effort": "high"},
        )

    def test_legacy_researcher_routes_to_librarian(self) -> None:
        resolved = self.configure.resolve_config({})
        self.assertEqual(
            self.configure.spawn_settings(resolved, "researcher"),
            self.configure.spawn_settings(resolved, "librarian"),
        )


class SkillPromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_eager_decomposition_is_a_required_gate(self) -> None:
        self.assertIn("## Mandatory decomposition pass", self.skill)
        self.assertIn("min_workers_nontrivial", self.skill)
        self.assertIn("no-delegation reason", self.skill)

    def test_role_model_routing_is_part_of_every_worker_packet(self) -> None:
        self.assertIn(".lunamaxing.json", self.skill)
        self.assertIn("model:", self.skill)
        self.assertIn("reasoning_effort:", self.skill)
        self.assertIn("**Oracle**", self.skill)
        self.assertIn("**Explorer**", self.skill)


if __name__ == "__main__":
    unittest.main()
