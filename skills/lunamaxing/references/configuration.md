# LunaMaxing model routing

LunaMaxing uses a project-local .lunamaxing.json file to choose the
orchestrator requirement, each specialist model, reasoning effort, and
delegation pressure. The file configures LunaMaxing's decisions; Codex still
enforces which models and reasoning levels are actually available.

## Create and inspect configuration

From the skill directory:

~~~text
python scripts/configure.py init <project-root>/.lunamaxing.json
python scripts/configure.py validate <project-root>/.lunamaxing.json
python scripts/configure.py resolve <project-root>/.lunamaxing.json
python scripts/configure.py spawn oracle <project-root>/.lunamaxing.json
~~~

The initializer refuses to overwrite an existing file. The example is validated
by assets/lunamaxing.schema.json and starts with a Luna-heavy mapping:

| Lane | Default model | Reasoning |
| --- | --- | --- |
| orchestrator | inherit current session | inherit |
| oracle | gpt-5.6-terra | max |
| explorer | gpt-5.6-luna | max |
| librarian | gpt-5.6-luna | max |
| designer | gpt-5.6-luna | max |
| fixer | gpt-5.6-luna | max |
| tester | gpt-5.6-luna | max |
| reviewer | gpt-5.6-luna | max |

Model strings are deliberately open: replace them with any model ID the current
Codex host accepts.

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
    "mode": "eager",
    "max_workers": 5,
    "min_workers_nontrivial": 1,
    "target_workers_complex": 3,
    "max_retries_per_packet": 1,
    "decompose_before_local": true
  }
}
~~~

Unspecified values inherit the packaged defaults. Unknown fields and unknown
agent names are rejected so a typo cannot silently change routing.

## Invocation overrides

An explicit invocation override has highest LunaMaxing precedence:

~~~text
$lunamaxing agents.oracle.model=gpt-5.6-terra agents.oracle.reasoning_effort=xhigh
$lunamaxing agents.fixer.model=gpt-5.6-luna delegation.max_workers=3
~~~

The helper accepts the same path=value syntax:

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
worker packet and passes them explicitly to the spawn call. Explicit spawn
values take precedence over Codex global subagent defaults.

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
max_concurrent_threads_per_session = 5
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
~~~

These defaults are useful for unconfigured children. LunaMaxing still sends
explicit per-role overrides, so Oracle can use Terra while the remaining lanes
use Luna.

Codex also supports project custom agents under .codex/agents/*.toml, with
model and model_reasoning_effort in each agent file. LunaMaxing does not
generate those files because explicit spawn overrides already provide per-run
routing without changing the user's Codex configuration.

## Delegation modes

- eager: decompose every non-trivial request and use at least
  min_workers_nontrivial whenever a safe packet and runtime are available.
- balanced: delegate multi-step, specialist, or parallel work; allow Sol to
  retain small bounded implementation.
- conservative: delegate only when specialization or parallelism materially
  changes quality or time.

All modes preserve dependency order, write ownership, verification, and the
configured max_workers ceiling.

## Compatibility and fallback

A configured reasoning level may not be supported by its selected model. When
the spawn tool rejects a combination, use that model's nearest available
reasoning level or the runtime default and record the fallback. Never claim that
a requested override was applied unless the spawn call accepted it.

Primary references:

- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
