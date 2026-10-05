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

For scripts, `init`, `validate`, `resolve`, `spawn <role>`, and `dispatch` are
available.
The packaged defaults are:

| Lane | Default model | Reasoning |
| --- | --- | --- |
| orchestrator | inherit current session | inherit |
| oracle | gpt-5.6-terra | max |
| explorer | gpt-6-luna | max |
| librarian | gpt-6-luna | max |
| designer | gpt-6-luna | max |
| fixer | gpt-6-luna | max |
| tester | gpt-6-luna | max |
| reviewer | gpt-6-luna | max |

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

Before every spawn, Sol resolves the project file and copies the role's model
and reasoning_effort into the actual tool arguments. Model names inside a
worker message do not select its runtime model. Without a project file, use
the packaged defaults. An invalid or explicitly named missing file must not
silently fall back.

To prepare a collaboration tool call, run from the skill directory:

~~~text
python scripts/configure.py dispatch fixer gps_restart /project/.lunamaxing.json \
  --message "Fix the GPS restart in the assigned files; include focused tests."
~~~

Omit the path only when using `.lunamaxing.json` in the current project root
or packaged defaults if it is absent. Output is a JSON object with canonical
`task_name`, concrete `model` and `reasoning_effort`, `message`, and
`fork_turns: "none"`. Pass it to the spawn tool; the helper itself does not
launch agents or intercept other tool calls. `--fork-turns 3` allows a bounded
history fork; `all` is rejected because the collaboration tool cannot apply
model overrides to a full-history fork.

The helper rejects unresolved `inherit` settings. If inheritance was explicitly
chosen by the user, establish and disclose the native route before spawning
directly. Runtime metadata—not the worker's prose—establishes the effective
model. Task names use prefixes such as `oracle_sqlite_review`; automatic
runtime nicknames are separate and may still be shown by the UI.

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
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "max"
~~~

These optional global defaults protect unconfigured children in all Codex
workflows. LunaMaxing does not change them during skill installation and
still sends concrete role settings explicitly.
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

A configured reasoning level may not be supported by its selected model.
When the spawn tool rejects routing, keep work local or obtain explicit
agreement on a specific fallback. If runtime metadata reports a different
model after launch, stop further launches on that route, disclose requested ->
effective, and preserve verified work without automatically re-running it.
Never claim an override applied based on the worker's self-report.

Version 0.6.1 changes unconfigured ordinary workers from inherit to Luna/max.
Existing project JSON values remain authoritative, including custom models
and explicit inherit choices. Re-generate optional native agent files if they
were produced from the old defaults.

Primary references:

- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)
