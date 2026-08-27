# LunaMaxing

<p align="center">
  <img src="assets/lunamax.png" alt="LunaMaxing logo" width="180">
</p>

Verification-first manager–worker orchestration for Codex.

LunaMaxing keeps strategic reasoning in **Sol**, delegates bounded execution to
specialized **Luna** workers, and accepts results only after evidence-based
verification.

## Use

Install or load the skill, then invoke:

~~~text
$lunamaxing
~~~

Use it when work can be decomposed into independent, low-coupling tasks. Keep
trivial, tightly coupled, ambiguous, and high-risk work with Sol.

## What it enforces

- Sol owns planning, architecture, integration, and final acceptance.
- Workers receive explicit scope, ownership, acceptance criteria, and validation.
- Parallelism is adaptive with a default ceiling of five workers.
- Workers do not recursively delegate or silently widen scope.
- Results require observable evidence; consensus is not verification.
- Retries are bounded; unresolved ambiguity escalates to Sol.
- Missing runtime capabilities trigger safe sequential/read-only fallbacks.
- Final checks inspect the actual diff and repository behavior.

## Resources

- [SKILL.md](skills/lunamaxing/SKILL.md) — entrypoint and decision procedure.
- [protocols.md](skills/lunamaxing/references/protocols.md) — packets, outputs,
  evidence, state transitions, retries, and ownership.
- [runtime-capabilities.md](skills/lunamaxing/references/runtime-capabilities.md) —
  capability preflight, model policy, fallbacks, and lifecycle limits.
- [librarian.md](skills/lunamaxing/references/librarian.md) — structural
  navigation and compressed repository evidence.
- [benchmarks.md](skills/lunamaxing/references/benchmarks.md) — measurable
  comparison plan and falsifiable success criteria.
- [evals.md](skills/lunamaxing/references/evals.md) — positive and negative
  behavioral evaluation cases.

## Local checks

From the skill directory:

~~~text
python scripts/validate_lunamax.py
python -m unittest discover -s tests -v
python scripts/check_packet.py packet.json --kind packet
python scripts/check_wave.py wave.json --max-workers 5
python scripts/check_state_log.py state-log.json
python scripts/benchmark.py init --output benchmark/runs.json
python scripts/benchmark.py validate benchmark/runs.json
python scripts/benchmark.py summary benchmark/runs.json
~~~

The benchmark helper summarizes recorded measurements; it never fabricates
worker runs or telemetry.

## Package structure

~~~text
lunamaxing/
├── .codex-plugin/plugin.json
├── assets/lunamax.png
└── skills/lunamaxing/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    ├── scripts/
    └── tests/
~~~

LunaMaxing is a thin policy over native Codex multi-agent primitives. It does
not include an MCP server, persistent scheduler, queue, or database.
