# LunaMaxing model routing

LunaMaxing uses an optional project-local `.lunamaxing.json` for orchestrator
requirements, specialist models, reasoning effort, and an optional explicit
worker ceiling. Codex decides which models and reasoning levels are available.

## Configure interactively

From the repository root, run:

~~~text
python skills/lunamaxing/scripts/configure.py interactive .lunamaxing.json
~~~

The offline wizard shows the current model and reasoning effort for the
orchestrator and all seven roles. Enter keeps a value, `inherit` uses Codex's
default, and any supported model ID can be typed. It validates and previews
the result, then asks before replacing an existing file.

For scripts, `init`, `validate`, `resolve`, and `spawn <role>` remain available.
The packaged defaults are:

| Lane | Default model | Reasoning |
| --- | --- | --- |
| orchestrator | inherit current session | inherit |
| oracle | gpt-5.6-terra | max |
| explorer | inherit | inherit |
| librarian | inherit | inherit |
| designer | inherit | inherit |
| fixer | inherit | inherit |
| tester | inherit | inherit |
| reviewer | inherit | inherit |

Model strings are deliberately open: replace them with any model ID the current
Codex host accepts.

GPT-6 Astra is available as `gpt-6-astra` and supports `low`, `medium`, `high`,
`xhigh`, and `max` reasoning in Codex. For example:

~~~json
{
  "agents": {
    "oracle": {
      "model": "gpt-6-astra",
      "reasoning_effort": "max"
    }
  }
}
~~~

## Configuration shape

~~~json
{
  "orchestrator": {
    "model": "inherit",
    "reasoning_effort": "inherit"
  },
  "agents": {
    "oracle": {
      "model": "gpt-5.6-terra",
      "reasoning_effort": "max"
    },
    "fixer": {
      "model": "gpt-5.6-luna",
      "reasoning_effort": "max"
    }
  },
  "delegation": {
    "mode": "balanced",
    "max_retries_per_packet": 1
  }
}
~~~

Unspecified values inherit the packaged defaults. Unknown fields and unknown
agent names are rejected so a typo cannot silently change routing. To set a
user ceiling, add a positive `delegation.max_workers`; `null` means no
LunaMaxing ceiling. The packaged configuration has no ceiling.

## Invocation overrides

An explicit invocation override has highest LunaMaxing precedence:

~~~text
$lunamaxing agents.oracle.model=gpt-5.6-terra agents.oracle.reasoning_effort=xhigh
$lunamaxing agents.oracle.model=gpt-6-astra agents.oracle.reasoning_effort=max
$lunamaxing agents.fixer.model=gpt-6-luna delegation.max_workers=3
~~~

The helper accepts the same path=value syntax and supports `max_workers` even
when that optional key is absent from the file:

~~~text
python scripts/configure.py resolve .lunamaxing.json \
  --set agents.oracle.model=gpt-5.6-terra \
  --set agents.fixer.reasoning_effort=high
~~~

Resolution order is:

1. packaged defaults;
2. project .lunamaxing.json;
3. explicit invocation or --set overrides.

After resolution, Sol copies each role's model and reasoning_effort into the
worker packet only when an explicit override is needed. A packet without
model fields uses inherit and the runtime default. Prefix
the runtime task name with the canonical role, for example
`oracle_sqlite_review`, and treat runtime metadata—not the worker's prose—as
the authoritative record of the model used. On mismatch, record
requested -> effective fallback and continue; never discard verified work
over a model label.

Native custom-agent files can override spawn settings. If you generated
`.codex/agents/*.toml`, regenerate those files after changing model routing,
or remove the stale role file before relying on an invocation override.

## Orchestrator model

A skill cannot replace the model of the parent session after that session has
started. Use one of these choices:

- keep orchestrator.model and reasoning_effort as inherit;
- select the desired model/reasoning in Codex before invoking LunaMaxing;
- set a concrete orchestrator requirement in .lunamaxing.json so Sol can
  detect and disclose a mismatch when its current model is observable.

For persistent Codex defaults, configure the main session separately:

~~~toml
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"
~~~

## Native Codex subagent defaults

Codex also supports global subagent defaults:

~~~toml
[agents]
enabled = true
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
~~~

These defaults are useful for unconfigured children. LunaMaxing sends explicit
overrides only for roles configured with concrete model or effort values.
Codex also accepts `agents.max_concurrent_threads_per_session` as an optional
native capacity setting. LunaMaxing does not set it or assume its default.

Codex also supports project custom agents under `.codex/agents/*.toml`, with
`model`, `model_reasoning_effort`, and `sandbox_mode` in each agent file.
`scripts/generate_agents.py` can create the seven optional native agent files
from the canonical role registry. It previews before writing and protects
existing files unless overwrite is explicitly requested. LunaMaxing works
without generated files. The generated model settings take precedence over
spawn overrides in Codex, so keep them in sync with `.lunamaxing.json`.
Tester has no fixed sandbox mode because a packet may explicitly authorize
test-only writes; packet ownership and the orchestrator must enforce that
boundary.

## Delegation modes

- eager: decompose every non-trivial request and dispatch useful ready work.
- balanced: delegate multi-step, specialist, or parallel work; allow Sol to
  retain small bounded implementation.
- conservative: delegate only when specialization or parallelism materially
  changes quality or time.

All modes preserve dependency order, write ownership, and verification. The
legacy fields `min_workers_nontrivial`, `target_workers_complex`, and
`decompose_before_local` are rejected with migration advice; remove them from
old project files. A prior explicit `max_workers` still works without the old
five-worker cap.

## Compatibility and fallback

A configured reasoning level may not be supported by its selected model. When
the spawn tool rejects a combination, use that model's nearest available
reasoning level only after disclosing the fallback. If runtime metadata reports
a different model after launch, record the requested -> effective fallback and
verify the work normally. Never claim that an override applied based on the
worker's self-report.

Primary references:

- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)
