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
validation commands comparable. The summary compares only task IDs present in
both strategies; it reports no speedup when there is no matched task. Record
unavailable settings instead of silently substituting another strategy.

## Reproducible cases

`assets/eval-cases.json` contains nine fixed task prompts and source trees:
trivial edit, reconnaissance, bounded bug, independent fixes, multi-module
feature, frontend plus backend, failed first attempt, risky review, and
external API research. Materialize a fresh copy for each strategy:

~~~text
python scripts/benchmark.py fixture bounded-bug-fix --output benchmark/sol-only
python scripts/benchmark.py fixture bounded-bug-fix --output benchmark/lunamaxing
~~~

Run each from the same initial files, model availability, and acceptance
criteria. Record actual observations in separate benchmark run records.

## Run record

Store measured objects per task/strategy in a top-level runs array. An empty
template contains no invented telemetry:

~~~json
{
  "schema_version": 1,
  "runs": []
}
~~~

Required fields:

- task_id, category, strategy;
- duration_s and total_tokens as non-negative numbers or null when unavailable;
- tests_passed and verified_useful as booleans or null when unavailable;
- regressions, human_review_defects, retries, write_conflicts, and
  worker_outputs_rejected as non-negative integers.
- delegation_mode, delegation_candidates, delegated_packets, worker_count,
  orchestrator_model, and the effective role_models mapping.

Unknown measurements must be null and excluded from averages; do not use zero
to hide missing telemetry. A run record is entered only after an actual run.

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
- delegation candidates, delegated packets, worker count, and delegation rate;
- requested/effective orchestrator and specialist model routing;
- verified-useful completion rate.

Useful derived values:

~~~text
parallel speedup = sol_baseline_duration / lunamaxing_duration
quality delta = lunamaxing_test_pass_rate - sol_baseline_test_pass_rate
context reduction = 1 - lunamaxing_context / sol_baseline_context
delegation rate = delegated_packets / delegation_candidates
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
