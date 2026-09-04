"""Tests for LunaMaxing's dependency-free validation helpers."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_lunamax = load_script("validate_lunamax")
check_packet = load_script("check_packet")
benchmark = load_script("benchmark")
check_wave = load_script("check_wave")
check_state_log = load_script("check_state_log")


class SkillValidationTests(unittest.TestCase):
    def test_complete_skill_passes(self) -> None:
        self.assertEqual(validate_lunamax.validate_skill(ROOT), [])


class PacketValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = {
            "role": "fixer",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "max",
            "objective": "Fix the parser",
            "scope": ["src/parser.py"],
            "do_not_touch": ["database/**"],
            "context": "The parser rejects escaped values.",
            "acceptance_criteria": ["escaped values parse"],
            "validation": ["python -m unittest"],
            "ownership": "src/parser.py",
            "dependencies": [],
            "output_contract": [
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
            ],
        }
        self.result = {
            "status": "DONE",
            "summary": "Parser fixed.",
            "model_used": "gpt-5.6-luna",
            "reasoning_effort_used": "max",
            "model_fallback": None,
            "files_changed": ["src/parser.py"],
            "tests_run": [{"command": "python -m unittest", "result": "pass"}],
            "evidence": [{"kind": "test", "claim": "regression passes"}],
            "assumptions": [],
            "unresolved_risks": [],
        }

    def test_valid_packet_and_result(self) -> None:
        self.assertEqual(check_packet.validate_packet(self.packet), [])
        self.assertEqual(
            check_packet.validate_result_against_packet(self.result, self.packet),
            [],
        )

    def test_out_of_scope_result_is_rejected(self) -> None:
        result = dict(self.result, files_changed=["src/other.py"])
        errors = check_packet.validate_result_against_packet(result, self.packet)
        self.assertTrue(any("outside packet scope" in error for error in errors))

    def test_read_only_packet_cannot_change_files(self) -> None:
        packet = dict(self.packet, read_only=True)
        result = dict(self.result)
        errors = check_packet.validate_result_against_packet(result, packet)
        self.assertTrue(any("read-only" in error for error in errors))

    def test_oracle_packet_accepts_explicit_model_routing(self) -> None:
        packet = dict(
            self.packet,
            role="oracle",
            read_only=True,
            model="gpt-5.6-terra",
            reasoning_effort="high",
        )
        self.assertEqual(check_packet.validate_packet(packet), [])

    def test_invalid_reasoning_effort_is_rejected(self) -> None:
        packet = dict(self.packet, reasoning_effort="turbo")
        errors = check_packet.validate_packet(packet)
        self.assertTrue(any("reasoning_effort" in error for error in errors))

    def test_missing_model_routing_is_rejected(self) -> None:
        packet = dict(self.packet)
        packet.pop("model")
        errors = check_packet.validate_packet(packet)
        self.assertTrue(any(error == "model" for error in errors))

    def test_result_must_report_effective_model(self) -> None:
        result = dict(self.result)
        result.pop("model_used")
        errors = check_packet.validate_result(result)
        self.assertIn("model_used", errors)

    def test_output_contract_requires_model_evidence(self) -> None:
        packet = dict(self.packet, output_contract=["status", "summary"])
        errors = check_packet.validate_packet(packet)
        self.assertTrue(any("output_contract missing" in error for error in errors))


class BenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run = {
            "task_id": "task-1",
            "category": "bug_fix",
            "strategy": "sol_high_luna",
            "duration_s": 10.0,
            "total_tokens": 100,
            "orchestrator_context_tokens": 50,
            "tool_calls": 4,
            "tests_passed": True,
            "regressions": 0,
            "human_review_defects": 0,
            "retries": 1,
            "write_conflicts": 0,
            "worker_outputs_rejected": 0,
            "verified_useful": True,
            "delegation_mode": "eager",
            "delegation_candidates": 2,
            "delegated_packets": 2,
            "worker_count": 2,
            "orchestrator_model": "gpt-5.6-sol",
            "role_models": {"fixer": "gpt-5.6-luna"},
        }

    def test_valid_dataset_and_summary(self) -> None:
        dataset = {"schema_version": 1, "runs": [self.run]}
        self.assertEqual(benchmark.validate_dataset(dataset), [])
        summary = benchmark.summarize_group(dataset["runs"])
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["tests_passed_rate"], 1.0)
        self.assertEqual(summary["delegation_rate"], 1.0)

    def test_negative_measurement_is_rejected(self) -> None:
        dataset = {"runs": [dict(self.run, duration_s=-1)]}
        errors = benchmark.validate_dataset(dataset)
        self.assertTrue(any("duration_s" in error for error in errors))

    def test_delegated_packets_cannot_exceed_candidates(self) -> None:
        dataset = {
            "runs": [
                dict(self.run, delegation_candidates=1, delegated_packets=2)
            ]
        }
        errors = benchmark.validate_dataset(dataset)
        self.assertTrue(any("delegated_packets" in error for error in errors))


class WaveValidationTests(unittest.TestCase):
    def packet(self, packet_id: str, ownership: str, dependency=None):
        return {
            "id": packet_id,
            "role": "fixer",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "max",
            "objective": "Make a bounded change",
            "scope": [ownership],
            "do_not_touch": [],
            "context": "The behavior is known.",
            "acceptance_criteria": ["the behavior is corrected"],
            "validation": ["python -m unittest"],
            "ownership": ownership,
            "dependencies": [] if dependency is None else [dependency],
            "output_contract": [
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
            ],
        }

    def test_disjoint_wave_passes(self) -> None:
        wave = [self.packet("a", "backend/**"), self.packet("b", "frontend/**")]
        self.assertEqual(check_wave.validate_wave(wave), [])

    def test_overlapping_writers_are_rejected(self) -> None:
        wave = [self.packet("a", "src/auth/**"), self.packet("b", "src/auth/token.py")]
        errors = check_wave.validate_wave(wave)
        self.assertTrue(any("ownership conflict" in error for error in errors))

    def test_same_wave_dependency_is_rejected(self) -> None:
        wave = [self.packet("a", "backend/**"), self.packet("b", "frontend/**", "a")]
        errors = check_wave.validate_wave(wave)
        self.assertTrue(any("later wave" in error for error in errors))


class StateLogTests(unittest.TestCase):
    def test_valid_done_path(self) -> None:
        states = [
            "UNDERSTAND",
            "CONFIGURE",
            "DECOMPOSE",
            "PLAN",
            "ROUTE",
            "DELEGATE",
            "EXECUTE",
            "COLLECT",
            "VERIFY",
            "INTEGRATE",
            "FINAL_VALIDATE",
            "DONE",
        ]
        self.assertEqual(check_state_log.validate_state_log(states), [])

    def test_retry_budget_and_terminal_state_are_enforced(self) -> None:
        states = ["UNDERSTAND", "CLASSIFY", "PLAN", "DELEGATE", "EXECUTE", "COLLECT", "VERIFY", "RETRY", "EXECUTE", "COLLECT", "VERIFY", "RETRY", "EXECUTE", "BLOCKED"]
        errors = check_state_log.validate_state_log(states, max_retries=1)
        self.assertTrue(any("budget" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
