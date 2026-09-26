# LunaMaxing

<p align="center">
  <img src="assets/lunamax.png" alt="LunaMaxing logo" width="180">
</p>

Verification-first manager–worker orchestration for Codex.

LunaMaxing turns the orchestrator into a planner and dispatcher. It decomposes
non-trivial goals into small specialist lanes, routes each lane to a configurable
model, and accepts results only after evidence-based verification.

## Use

Install or load the skill, then invoke:

~~~text
$lunamaxing
~~~

Only a truly isolated, clear, low-risk action stays entirely in the
orchestrator. Non-trivial work receives a decomposition pass first; coupled work
can still delegate discovery, testing, review, or architectural analysis.

The orchestrator can continue integration or other non-overlapping work while
specialists run. Independent packets launch in the same wave; dependent packets
wait for the preceding wave. Actual concurrency is limited by Codex and safe
file ownership, not by a LunaMaxing default worker count.

## Download

[Download LunaMaxing 0.6.0](https://github.com/AndreaScuto/lunamaxing/releases/download/v0.6.0/LunaMaxing-0.6.0.zip)

## Model routing

Configure the orchestrator and all seven specialists interactively:

~~~text
python skills/lunamaxing/scripts/configure.py interactive .lunamaxing.json
~~~

The default inherits Codex's model for the orchestrator and ordinary workers;
Oracle uses `gpt-5.6-terra` with max reasoning for escalation. The wizard
accepts any model ID supported by your Codex host. You can also override a
value for one invocation:

~~~text
$lunamaxing agents.oracle.model=gpt-5.6-terra agents.fixer.model=gpt-5.6-luna
$lunamaxing agents.oracle.model=gpt-6-astra agents.oracle.reasoning_effort=max
~~~

`gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna` can be selected when available on
your Codex host. Concrete configured values become explicit spawn overrides;
`inherit` uses native Codex defaults. The runtime model shown by Codex is the
effective model, regardless of a worker's self-description.

For example, this project profile puts the orchestrator on Sol/medium, Oracle
on Sol/high, and every other specialist on Luna/max:

~~~json
{
  "orchestrator": {"model": "gpt-6-sol", "reasoning_effort": "medium"},
  "agents": {
    "oracle": {"model": "gpt-6-sol", "reasoning_effort": "high"},
    "explorer": {"model": "gpt-6-luna", "reasoning_effort": "max"},
    "librarian": {"model": "gpt-6-luna", "reasoning_effort": "max"},
    "designer": {"model": "gpt-6-luna", "reasoning_effort": "max"},
    "fixer": {"model": "gpt-6-luna", "reasoning_effort": "max"},
    "tester": {"model": "gpt-6-luna", "reasoning_effort": "max"},
    "reviewer": {"model": "gpt-6-luna", "reasoning_effort": "max"}
  }
}
~~~

Save it as `.lunamaxing.json` in the project root, or use the interactive
wizard above to choose the values. Validate with
`python skills/lunamaxing/scripts/configure.py validate .lunamaxing.json`.

The orchestrator model inherits the current Codex session by default because a
skill cannot switch its already-running parent model.

To preview optional native specialist agents for a project:

~~~text
python skills/lunamaxing/scripts/generate_agents.py <project-root> --dry-run
~~~

Run the same command without `--dry-run` to create `.codex/agents/*.toml`.
Existing files are protected unless `--force` is supplied.
Generated agent files can take precedence over spawn overrides; regenerate
them after changing model routing. Tester has no fixed read-only sandbox in
those files because a packet may explicitly authorize test-only writes.

The lane-based routing and scheduler-first boundary are inspired by
[oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim),
adapted to native Codex subagents and explicit per-spawn model overrides.

## What it enforces

- Sol owns planning, architecture, integration, and final acceptance.
- Every non-trivial task is decomposed before Sol may keep work locally.
- Workers receive explicit scope, exclusions, acceptance criteria, and validation.
- Writable workers require explicit, non-overlapping ownership; read-only roles
  cannot be made writable by a packet.
- Model and reasoning settings are configurable per role.
- Useful independent packets are dispatched without a LunaMaxing default
  ceiling; Codex enforces actual runtime capacity.
- Workers do not recursively delegate or silently widen scope.
- Results require observable evidence; consensus is not verification.
- A Git helper can check actual changed paths against packet scope and ownership.
- Retries are bounded; unresolved ambiguity escalates to Sol.
- Missing runtime capabilities trigger safe sequential/read-only fallbacks.
- Final checks inspect the actual diff and repository behavior.

## Resources

- [CHANGELOG.md](CHANGELOG.md) — release notes.
- [SKILL.md](skills/lunamaxing/SKILL.md) — entrypoint and decision procedure.
- [decomposition.md](skills/lunamaxing/references/decomposition.md) — Luna-first
  lane splitting, routing, waves, and the no-delegation gate.
- [protocols.md](skills/lunamaxing/references/protocols.md) — packets, outputs,
  evidence, state transitions, retries, and ownership.
- [runtime-capabilities.md](skills/lunamaxing/references/runtime-capabilities.md) —
  capability preflight, model policy, fallbacks, and lifecycle limits.
- [librarian.md](skills/lunamaxing/references/librarian.md) — separate Explorer
  repository navigation and Librarian external-research contracts.
- [benchmarks.md](skills/lunamaxing/references/benchmarks.md) — measurable
  comparison plan and falsifiable success criteria.
- [evals.md](skills/lunamaxing/references/evals.md) — positive and negative
  behavioral evaluation cases.
- [configuration.md](skills/lunamaxing/references/configuration.md) — policy
  defaults, per-role models, overrides, and safe runtime mapping.
- [runtime-notes.md](skills/lunamaxing/references/runtime-notes.md) — dated
  lifecycle assumptions and primary references.

## Local checks

From the skill directory:

~~~text
python scripts/validate_lunamax.py
python -m unittest discover -s tests -v
python scripts/configure.py interactive <project-root>/.lunamaxing.json
python scripts/configure.py validate <project-root>/.lunamaxing.json
python scripts/check_packet.py packet.json --kind packet
python scripts/check_wave.py wave.json
python scripts/check_git.py packet.json --repo <project-root>
python scripts/check_state_log.py state-log.json
python scripts/generate_agents.py --help
python scripts/benchmark.py fixture bounded-bug-fix --output benchmark/case-1
python scripts/benchmark.py init --output benchmark/runs.json
python scripts/benchmark.py validate benchmark/runs.json
python scripts/benchmark.py summary benchmark/runs.json
~~~

The benchmark helper summarizes recorded measurements; it never fabricates
worker runs or telemetry. Native agent generation is optional and refuses to
overwrite existing `.codex/agents` files without an explicit override.

## Package structure

~~~text
lunamaxing/
├── .codex-plugin/plugin.json
├── assets/lunamax.png
└── skills/lunamaxing/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/
    ├── references/
    ├── scripts/
    └── tests/
~~~

LunaMaxing is a thin policy over native Codex multi-agent primitives. It does
not include an MCP server, persistent scheduler, queue, or database.
