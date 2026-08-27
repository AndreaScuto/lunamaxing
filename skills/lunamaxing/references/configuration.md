# LunaMaxing configuration philosophy

This file describes policy defaults, not a guaranteed Codex configuration schema.
Translate them only to keys and flags documented by the runtime in use.

## Conceptual defaults

~~~toml
[lunamaxing]
orchestrator_model = "strongest-available"
orchestrator_reasoning = "high"
worker_model = "strongest-available-worker"
worker_reasoning = "max"
max_workers = 5
max_retries_per_packet = 1
parallel_by_default = true
recursive_delegation = false
verification_required = true
~~~

The names above are policy concepts. Do not paste them into a runtime config
unless that runtime documents the exact section and key names.

## Precedence

Apply settings in this order:

1. runtime-enforced limits and safety/approval controls;
2. explicit user constraints for the current task;
3. project or workspace configuration;
4. LunaMaxing defaults;
5. Sol's task-specific decision.

A lower layer must never override a higher layer's safety boundary. A user
request to keep work local or sequential wins over parallel_by_default.

## Task-level overrides

Sol may lower the worker ceiling, retry budget, or tool scope for a task:

~~~yaml
task_overrides:
  max_workers: 2
  max_retries_per_packet: 0
  require_read_only_review: true
~~~

Sol should not increase a runtime ceiling, bypass an approval boundary, or claim
that a child model/reasoning override succeeded when the runtime rejected it.

## Cost-aware fan-out

Reduce fan-out when the packet is cheap, validation is expensive, workers need
coordination, or maximum reasoning would exceed the available budget. Prefer a
single high-quality worker over several redundant workers. Record retries and
rejected outputs in the final report so benchmark data includes orchestration
cost.

## Capability mapping

Before changing configuration, map each desired setting to a verified runtime
capability:

| Policy need | Required evidence |
| --- | --- |
| max_workers | documented concurrency limit or successful bounded spawn |
| worker model/reasoning | accepted per-child override or runtime configuration |
| parallel_by_default | nonblocking spawn and safe collection behavior |
| isolated writes | distinct worktree/checkout confirmed for each worker |
| completion notification | documented callback/wake-up or observed event |
| verification_required | Sol procedure and repository checks, not a config flag alone |

If the mapping is unknown, leave the setting at the safer default and state the
uncertainty.
