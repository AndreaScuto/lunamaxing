# Benchmark plan

Use this reference before claiming that LunaMaxing is faster, cheaper, or more
reliable. A benchmark must measure the complete Sol workflow, including
orchestration overhead and rejected worker output.

## Hypothesis

LunaMaxing should improve verified useful output per unit of time, cost, and
orchestrator context on decomposable tasks, while avoiding orchestration on
trivial or tightly coupled tasks.

Do not claim an improvement from agent count or from a single successful run.

## Comparison matrix

Run representative tasks with:

| Strategy | Meaning |
| --- | --- |
| sol_high | Sol alone at high reasoning |
| sol_xhigh | Sol alone at xhigh reasoning |
| sol_high_luna | Sol high plus bounded Luna workers |
| sol_xhigh_luna | Sol xhigh plus bounded Luna workers |

Keep the repository revision, task prompt, tools, model availability, and
validation commands comparable. Record unavailable settings instead of
silently substituting another strategy.

## Task categories

Include multiple examples of:

- simple bug fix;
- multi-module feature;
- refactor;
- test expansion;
- documentation/API research;
- frontend plus backend work;
- ambiguous production bug;
- code review;
- trivial one-file edit as a no-delegation control.

Each task needs a fixed prompt, acceptance criteria, validation commands, and a
fresh or resettable repository state.

## Run record

Store one JSON object per task/strategy in a file with a top-level runs array:

~~~json
{
  "task_id": "auth-refresh-001",
  "category": "bug_fix",
  "strategy": "sol_high_luna",
  "duration_s": 312.4,
  "total_tokens": 18400,
  "orchestrator_context_tokens": 9200,
  "tool_calls": 27,
  "tests_passed": true,
  "regressions": 0,
  "human_review_defects": 0,
  "retries": 1,
  "write_conflicts": 0,
  "worker_outputs_rejected": 1,
  "verified_useful": true,
  "notes": "Two independent packets; one retry after scope correction."
}
~~~

Required fields:

- task_id, category, strategy;
- duration_s and total_tokens as non-negative numbers;
- tests_passed and verified_useful as booleans;
- regressions, human_review_defects, retries, write_conflicts, and
  worker_outputs_rejected as non-negative integers.

Unknown measurements must be null in an extension field and excluded from
averages; do not use zero to hide missing telemetry.

## Metrics

Report by strategy and by task category:

- wall-clock duration;
- total token/credit usage when observable;
- orchestrator context growth;
- tool-call count;
- test pass rate;
- regression count;
- human-review defects;
- retry count;
- write/merge conflicts;
- worker outputs rejected by Sol;
- verified-useful completion rate.

Useful derived values:

~~~text
parallel speedup = sol_baseline_duration / lunamaxing_duration
quality delta = lunamaxing_test_pass_rate - sol_baseline_test_pass_rate
context reduction = 1 - lunamaxing_context / sol_baseline_context
~~~

Do not calculate a metric when its denominator is missing or zero. Report the
sample count beside every average.

## Success and falsification

LunaMaxing is useful for a category only when repeated runs show a meaningful
time, context, or quality advantage without unacceptable regressions,
conflicts, retries, or cost growth.

It is a success if at least one decomposable category improves while:

- final test/review quality is equal or better;
- conflict and rejection rates remain acceptable;
- orchestration overhead does not erase the gain.

It is falsified for a category when LunaMaxing is slower, more expensive, less
reliable, or harder to verify than the best Sol-only baseline. Teach the policy
to choose local or sequential execution for that category.

## Repeatable commands

From the skill directory:

~~~text
python scripts/benchmark.py init --output benchmark/runs.json
python scripts/benchmark.py validate benchmark/runs.json
python scripts/benchmark.py summary benchmark/runs.json
python scripts/benchmark.py summary benchmark/runs.json --baseline sol_xhigh --candidate sol_high_luna
~~~

The benchmark script summarizes recorded runs; it does not pretend to execute
Codex workers or fabricate telemetry.
