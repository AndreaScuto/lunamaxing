# Runtime capabilities and fallbacks

Read this reference before delegating a real wave. LunaMaxing must adapt to the
runtime that is actually available; it must not assume that a desirable
multi-agent feature exists.

## Capability preflight

Record a yes/no/unknown result for each capability:

| Capability | Why it matters | If missing |
| --- | --- | --- |
| parallel spawn | launches independent packets together | run one packet at a time |
| nonblocking child execution | lets Sol do useful work while children run | keep the wave small and collect at explicit safe points |
| completion notification | tells Sol when a child is ready | poll/collect only while the active turn remains open |
| per-child model override | selects the configured role model | use runtime default and record fallback |
| per-child reasoning override | selects configured effort | use runtime default and record fallback |
| structured child result | preserves status and evidence fields | require a strict text/YAML contract |
| isolated workdir | prevents write collisions | disjoint ownership and serialized overlap |
| child cancellation | stops stale or unsafe work | do not start risky packets without a manual stop path |
| tool approval boundary | limits external/destructive actions | use read-only packets or ask Sol to execute |

Unknown is not yes. When a capability cannot be verified from the current
tooling or documentation, choose the safer fallback.

## Execution matrix

| Available shape | Preferred behavior |
| --- | --- |
| spawn + nonblocking + notification | launch one complete ready wave, continue Sol work, collect on readiness |
| spawn but blocking only | launch fewer packets and collect before dependent work |
| no spawn | keep the complete plan in Sol; execute sequentially |
| spawn without isolation | give every writer a disjoint path; make reviewers read-only |
| no per-child overrides | disclose the limitation; never claim role-specific routing occurred |
| no completion notification | never promise wake-up after the turn; collect before the turn ends |
| no structured result | paste the output contract into the packet and normalize manually |
| unavailable test/build tools | mark validation not-run and escalate rather than claiming pass |

Dispatch useful independent packets; Codex decides how many can run. The native
`agents.max_concurrent_threads_per_session` setting can cap open subagents.
Official docs do not guarantee automatic queuing above that cap, so a failed
spawn is a capacity signal, not evidence that a packet is running.

## Model and reasoning selection

Resolve .lunamaxing.json before spawning and pass each role's model and
reasoning_effort explicitly only when an override is needed. Otherwise use
inherit and the runtime default. A mismatch between requested and effective
model is recorded as fallback, never a reason to discard verified work.

Codex supports agents.default_subagent_model and
agents.default_subagent_reasoning_effort as global fallbacks, while explicit
spawn values take precedence. Custom Codex agent files may also define model
and model_reasoning_effort. Custom agent file values can take precedence over
spawn overrides; inspect the effective runtime model. Do not invent other
runtime keys.

The orchestrator is the already-running parent session; the skill cannot switch
its model mid-turn. A configured concrete orchestrator model is therefore a
launch requirement, while inherit accepts the current session.

If a configured model or reasoning effort is unavailable, record requested ->
effective and preserve the role. A model mismatch alone does not invalidate
verified work. Worker prose is never evidence of its runtime model. A model
override never transfers final authority away from Sol.

## Background versus active parallelism

These are different promises:

~~~text
ACTIVE PARALLELISM
Sol and child workers run during the same live orchestration turn.
Sol collects and verifies results before deciding completion.

AUTONOMOUS BACKGROUND
Children continue after the foreground turn ends and reliably wake Sol to
resume, verify, and report without user interaction.
~~~

Use the first when supported. Treat the second as unavailable unless the
runtime explicitly guarantees child lifecycle, persistence, notification, and
resumption. Never tell the user that work will continue later on its own.

## Worktree and write safety

When isolated worktrees are available:

1. assign one ownership domain to each writer;
2. require the worker to report its branch/worktree and changed files;
3. compare the worker diff against the packet before integration;
4. merge only after Sol verification.

When isolated worktrees are not available:

1. assign disjoint paths or symbols;
2. serialize overlapping work;
3. let reviewers/testers read without editing;
4. inspect the shared diff after every accepted result;
5. stop on generated-file or lockfile conflicts.

Never resolve an ownership conflict by silently accepting the last write.

## Cost and resource guardrails

Useful concurrent work is bounded by:

~~~text
independent ready tasks + native runtime capacity + write safety
~~~

There is no LunaMaxing default worker ceiling. An explicit user
`delegation.max_workers` value may further limit a run. Use zero workers for
trivial work. Reduce fan-out when:

- packets need frequent coordination;
- workers contend for the same files;
- validation is expensive relative to the work;
- max reasoning would exceed the available token/credit budget;
- the task is ambiguous enough that Sol should decide first.

Do not build a scheduler, persistent queue, or database to compensate for a
missing runtime feature. A smaller or sequential wave is the intended fallback.
