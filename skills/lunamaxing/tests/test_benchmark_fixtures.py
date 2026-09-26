"""Benchmark fixtures are reproducible and contain no invented runs."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark.py"


def load_benchmark():
    spec = importlib.util.spec_from_file_location("benchmark_fixtures", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureTests(unittest.TestCase):
    def test_nine_cases_and_materialization(self):
        benchmark = load_benchmark()
        cases = benchmark.load_cases()
        self.assertEqual(len(cases), 9)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "case"
            benchmark.materialize_case("bounded-bug-fix", target)
            self.assertTrue((target / "TASK.md").is_file())
            self.assertTrue((target / "src" / "parser.py").is_file())
            with self.assertRaises(FileExistsError):
                benchmark.materialize_case("bounded-bug-fix", target)

    def test_missing_telemetry_is_null_not_zero(self):
        benchmark = load_benchmark()
        run = {field: None for field in benchmark.REQUIRED_FIELDS}
        run.update({
            "task_id": "bounded-bug-fix",
            "category": "bug_fix",
            "strategy": "sol_only",
            "delegation_mode": "balanced",
            "orchestrator_model": "gpt-6-sol",
            "role_models": {},
        })
        self.assertEqual(benchmark.validate_dataset({"runs": [run]}), [])
        summary = benchmark.summarize_group([run])
        self.assertIsNone(summary["mean_total_tokens"])
        self.assertEqual(summary["n_total_tokens"], 0)
        self.assertIsNone(summary["tests_passed_rate"])

    def test_missing_delegated_count_is_not_zero(self):
        benchmark = load_benchmark()
        summary = benchmark.summarize_group([{
            "delegation_candidates": 2,
            "delegated_packets": None,
        }])
        self.assertIsNone(summary["delegation_rate"])

    def test_fixture_rejects_windows_escape_path(self):
        benchmark = load_benchmark()
        original = benchmark.load_cases
        cases = [{
            "id": "escape", "files": {path: "bad"},
            "prompt": "test", "acceptance": [], "validation": [],
        } for path in ("..\\..\\victim", "C:\\victim")]
        try:
            with tempfile.TemporaryDirectory() as temporary:
                for case in cases:
                    benchmark.load_cases = lambda case=case: [case]
                    with self.assertRaises(ValueError):
                        benchmark.materialize_case("escape", Path(temporary) / "case")
        finally:
            benchmark.load_cases = original

    def test_comparison_only_uses_matching_task_ids(self):
        benchmark = load_benchmark()
        baseline = [{"task_id": "a", "duration_s": 10.0}]
        candidate = [{"task_id": "b", "duration_s": 1.0}]
        comparison = benchmark.compare_groups(baseline, candidate)
        self.assertEqual(comparison["matched_task_count"], 0)
        self.assertIsNone(comparison["duration_speedup"])


if __name__ == "__main__":
    unittest.main()
