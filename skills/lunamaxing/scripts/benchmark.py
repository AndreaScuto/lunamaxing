#!/usr/bin/env python3
"""Record and summarize LunaMaxing benchmark runs without fabricating telemetry."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable

REQUIRED_FIELDS = (
    "task_id",
    "category",
    "strategy",
    "duration_s",
    "total_tokens",
    "orchestrator_context_tokens",
    "tool_calls",
    "tests_passed",
    "regressions",
    "human_review_defects",
    "retries",
    "write_conflicts",
    "worker_outputs_rejected",
    "verified_useful",
    "delegation_mode",
    "delegation_candidates",
    "delegated_packets",
    "worker_count",
    "orchestrator_model",
    "role_models",
)
NUMERIC_FIELDS = (
    "duration_s",
    "total_tokens",
    "orchestrator_context_tokens",
    "tool_calls",
    "regressions",
    "human_review_defects",
    "retries",
    "write_conflicts",
    "worker_outputs_rejected",
    "delegation_candidates",
    "delegated_packets",
    "worker_count",
)
INTEGER_FIELDS = (
    "tool_calls",
    "regressions",
    "human_review_defects",
    "retries",
    "write_conflicts",
    "worker_outputs_rejected",
    "delegation_candidates",
    "delegated_packets",
    "worker_count",
)
BOOLEAN_FIELDS = ("tests_passed", "verified_useful")


def main() -> int:
    args = parse_args()
    if args.command == "init":
        return init_dataset(args.output)
    try:
        dataset = load_dataset(args.path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return emit_errors(args, [str(exc)])
    errors = validate_dataset(dataset)
    if args.command == "validate":
        return emit_errors(args, errors)
    if errors:
        return emit_errors(args, errors)
    return summarize(dataset, args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create an empty benchmark file")
    init_parser.add_argument("--output", type=Path, required=True)

    validate_parser = subparsers.add_parser("validate", help="validate recorded runs")
    validate_parser.add_argument("path", type=Path)
    validate_parser.add_argument("--json", action="store_true", dest="as_json")

    summary_parser = subparsers.add_parser("summary", help="summarize recorded runs")
    summary_parser.add_argument("path", type=Path)
    summary_parser.add_argument("--baseline")
    summary_parser.add_argument("--candidate")
    summary_parser.add_argument("--by-category", action="store_true")
    summary_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def init_dataset(output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    template = {
        "schema_version": 1,
        "description": "Add measured runs; unknown measurements must remain null.",
        "runs": [],
    }
    output.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    print(f"Benchmark template written to {output}")
    return 0


def load_dataset(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("benchmark file must contain a JSON object")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise ValueError("benchmark file must contain a top-level runs array")
    return payload


def validate_dataset(dataset: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, run in enumerate(dataset.get("runs", [])):
        if not isinstance(run, dict):
            errors.append(f"runs[{index}] must be an object")
            continue
        missing = [field for field in REQUIRED_FIELDS if field not in run]
        errors.extend(f"runs[{index}] missing {field}" for field in missing)
        errors.extend(validate_run(index, run))
    return sorted(set(errors))


def validate_run(index: int, run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("task_id", "category", "strategy"):
        if not isinstance(run.get(field), str) or not run[field].strip():
            errors.append(f"runs[{index}].{field} must be a non-empty string")
    for field in NUMERIC_FIELDS:
        value = run.get(field)
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0
        ):
            errors.append(f"runs[{index}].{field} must be a non-negative number or null")
    for field in INTEGER_FIELDS:
        value = run.get(field)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            errors.append(f"runs[{index}].{field} must be a non-negative integer or null")
    for field in BOOLEAN_FIELDS:
        value = run.get(field)
        if not isinstance(value, bool):
            errors.append(f"runs[{index}].{field} must be boolean")
    mode = run.get("delegation_mode")
    if mode not in {"conservative", "balanced", "eager"}:
        errors.append(
            f"runs[{index}].delegation_mode must be conservative, balanced, or eager"
        )
    orchestrator = run.get("orchestrator_model")
    if not isinstance(orchestrator, str) or not orchestrator.strip():
        errors.append(f"runs[{index}].orchestrator_model must be non-empty")
    role_models = run.get("role_models")
    if not isinstance(role_models, dict) or not all(
        isinstance(role, str)
        and role.strip()
        and isinstance(model, str)
        and model.strip()
        for role, model in role_models.items()
    ):
        errors.append(f"runs[{index}].role_models must map roles to model strings")
    candidates = run.get("delegation_candidates")
    delegated = run.get("delegated_packets")
    if (
        isinstance(candidates, int)
        and not isinstance(candidates, bool)
        and isinstance(delegated, int)
        and not isinstance(delegated, bool)
        and delegated > candidates
    ):
        errors.append(
            f"runs[{index}].delegated_packets cannot exceed delegation_candidates"
        )
    return errors


def emit_errors(args: argparse.Namespace, errors: list[str]) -> int:
    if getattr(args, "as_json", False):
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    elif errors:
        print("Benchmark validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Benchmark validation passed")
    return 1 if errors else 0


def summarize(dataset: dict[str, Any], args: argparse.Namespace) -> int:
    if args.by_category and (args.baseline or args.candidate):
        return emit_errors(
            args,
            ["--by-category cannot be combined with --baseline/--candidate"],
        )
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in dataset["runs"]:
        groups.setdefault(run["strategy"], []).append(run)

    if args.by_category:
        category_groups: dict[str, list[dict[str, Any]]] = {}
        for run in dataset["runs"]:
            category_groups.setdefault(
                f"{run['category']} / {run['strategy']}", []
            ).append(run)
        groups = category_groups

    summaries = {
        key: summarize_group(runs)
        for key, runs in sorted(groups.items())
    }
    comparison = None
    if args.baseline or args.candidate:
        if not args.baseline or not args.candidate:
            return emit_errors(
                args, ["--baseline and --candidate must be provided together"]
            )
        if args.baseline not in groups or args.candidate not in groups:
            return emit_errors(
                args,
                [
                    "comparison strategies must exist in the selected summary "
                    "groups"
                ],
            )
        comparison = compare_groups(groups[args.baseline], groups[args.candidate])

    payload = {"groups": summaries}
    if comparison is not None:
        payload["comparison"] = comparison
    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print_summary(summaries, comparison)
    return 0


def summarize_group(runs: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"count": len(runs)}
    for field in NUMERIC_FIELDS:
        values = available_numbers(runs, field)
        if values:
            summary[f"mean_{field}"] = round(statistics.fmean(values), 3)
            summary[f"median_{field}"] = round(statistics.median(values), 3)
            summary[f"n_{field}"] = len(values)
        else:
            summary[f"mean_{field}"] = None
            summary[f"median_{field}"] = None
            summary[f"n_{field}"] = 0
    for field in BOOLEAN_FIELDS:
        values = [run[field] for run in runs if isinstance(run.get(field), bool)]
        summary[f"{field}_rate"] = (
            round(sum(values) / len(values), 3) if values else None
        )
        summary[f"n_{field}"] = len(values)
    candidates = sum(
        run["delegation_candidates"]
        for run in runs
        if isinstance(run.get("delegation_candidates"), int)
        and not isinstance(run["delegation_candidates"], bool)
    )
    delegated = sum(
        run["delegated_packets"]
        for run in runs
        if isinstance(run.get("delegated_packets"), int)
        and not isinstance(run["delegated_packets"], bool)
    )
    summary["delegation_rate"] = (
        round(delegated / candidates, 3) if candidates else None
    )
    return summary


def available_numbers(runs: Iterable[dict[str, Any]], field: str) -> list[float]:
    return [
        float(run[field])
        for run in runs
        if isinstance(run.get(field), (int, float)) and not isinstance(run[field], bool)
    ]


def compare_groups(
    baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]
) -> dict[str, Any]:
    base = summarize_group(baseline)
    current = summarize_group(candidate)
    return {
        "baseline_count": len(baseline),
        "candidate_count": len(candidate),
        "duration_speedup": ratio(
            base["mean_duration_s"], current["mean_duration_s"]
        ),
        "quality_delta": difference(
            current["tests_passed_rate"], base["tests_passed_rate"]
        ),
        "verified_useful_delta": difference(
            current["verified_useful_rate"], base["verified_useful_rate"]
        ),
        "context_reduction": reduction(
            base["mean_orchestrator_context_tokens"],
            current["mean_orchestrator_context_tokens"],
        ),
        "retry_delta": difference(
            current["mean_retries"], base["mean_retries"]
        ),
        "conflict_delta": difference(
            current["mean_write_conflicts"], base["mean_write_conflicts"]
        ),
        "delegation_rate_delta": difference(
            current["delegation_rate"], base["delegation_rate"]
        ),
    }


def ratio(baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None or candidate <= 0:
        return None
    return round(baseline / candidate, 3)


def reduction(baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None or baseline == 0:
        return None
    return round(1 - candidate / baseline, 3)


def difference(candidate: float | None, baseline: float | None) -> float | None:
    if candidate is None or baseline is None:
        return None
    return round(candidate - baseline, 3)


def print_summary(
    summaries: dict[str, dict[str, Any]], comparison: dict[str, Any] | None
) -> None:
    print("strategy | n | duration_s | context_tokens | delegated | tests_passed | useful")
    print("--- | ---: | ---: | ---: | ---: | ---: | ---:")
    for strategy, summary in summaries.items():
        print(
            f"{strategy} | {summary['count']} | "
            f"{display(summary['mean_duration_s'])} | "
            f"{display(summary['mean_orchestrator_context_tokens'])} | "
            f"{display(summary['delegation_rate'])} | "
            f"{display(summary['tests_passed_rate'])} | "
            f"{display(summary['verified_useful_rate'])}"
        )
    if comparison is not None:
        print("\ncomparison")
        for key, value in comparison.items():
            print(f"- {key}: {value}")


def display(value: Any) -> str:
    return "n/a" if value is None else str(value)


if __name__ == "__main__":
    raise SystemExit(main())
