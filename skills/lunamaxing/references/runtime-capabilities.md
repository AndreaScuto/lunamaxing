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
| per-child model override | selects Luna for narrow work | use runtime default |
| per-child reasoning override | reserves maximum effort for workers | use runtime default |
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
| no per-child overrides | use the strongest available defaults and disclose that no override occurred |
| no completion notification | never promise wake-up after the turn; collect before the turn ends |
| no structured result | paste the output contract into the packet and normalize manually |
| unavailable test/build tools | mark validation not-run and escalate rather than claiming pass |

The preferred strategy is always bounded parallelism, not maximum parallelism.

## Model and reasoning selection

Use capability-aware preferences:

- Sol: strongest available model at high or xhigh reasoning when global
  architecture, ambiguity, integration, or verification dominates.
- Luna: strongest available worker model at maximum reasoning when the packet is
  narrow and independently verifiable.
- If the runtime exposes no named Sol/Luna models, preserve the role split in
  the packet and use the available model without inventing a setting.
- Do not encode a made-up TOML key, CLI flag, or model identifier in a skill
  instruction. Map configuration only to keys documented by the current runtime.
- A model override is a preference, not an authority transfer: Sol still owns
  acceptance.

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

Worker count is bounded by:

~~~text
min(independent_ready_tasks, configured_ceiling, runtime_limit)
~~~

Use zero workers for trivial work. Reduce fan-out when:

- packets need frequent coordination;
- workers contend for the same files;
- validation is expensive relative to the work;
- max reasoning would exceed the available token/credit budget;
- the task is ambiguous enough that Sol should decide first.

Do not build a scheduler, persistent queue, or database to compensate for a
missing runtime feature. A smaller or sequential wave is the intended fallback.
