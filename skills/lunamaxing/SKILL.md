---
name: lunamaxing
description: Orchestrate decomposable coding work with a strong manager and bounded Luna workers, using explicit task packets, evidence gates, adaptive parallelism, and Sol-owned final verification. Use when work is independently verifiable; skip trivial, tightly coupled, or purely sequential tasks.
---

# LunaMaxing

LunaMaxing is a verification-first manager–worker policy:

~~~text
Sol (global context, decisions, integration)
  -> Luna workers (bounded execution and evidence)
  -> Sol (verification, integration, final acceptance)
~~~

The manager is the authority. A worker result is a candidate plus evidence,
never an accepted fact.

## Apply the smallest useful mode

Classify the user's task before delegating:

1. **Local** — do trivial, one-file, tightly coupled, high-risk, or ambiguous
   work in Sol. A narrow read-only investigation is the only delegation that
   may help an otherwise sequential task.
2. **Sequential** — keep dependent steps in Sol or execute them as ordered
   waves. Do not manufacture parallelism.
3. **Delegated** — build a dependency graph and delegate only ready nodes that
   are bounded, low-coupling, context-light, recoverable, and independently
   verifiable.

The orchestration tax is real. Use zero workers when direct execution is
faster, safer, or clearer.

## Authority and non-goals

- Sol owns the user objective, repository-wide context, decomposition,
  architecture, prioritization, ambiguity, conflict resolution, integration,
  risk management, and the decision that the whole task is complete.
- Workers execute a packet. They do not plan the whole task, recursively spawn
  workers, negotiate with peers, silently widen scope, or approve completion.
- Never build a swarm, persistent scheduler, queue, database, message bus, or
  autonomous post-turn promise for this skill. Use native runtime primitives
  and safe fallbacks.
- Consensus is not verification. Agent count is not a confidence metric.

## Runtime and model policy

- Prefer the strongest available orchestrator at high or xhigh reasoning. The
  target is Sol/GPT-5.6 when that model exists, but never claim an unavailable
  model or reasoning override.
- Prefer Luna/GPT-5.6 at maximum reasoning for narrow worker packets when the
  runtime supports per-child overrides. Otherwise use the available runtime
  defaults without pretending an override occurred.
- Treat max_workers = 5 as a ceiling, not a target:
  0..min(independent_ready_tasks, configured_ceiling, runtime_limit) workers.
- Treat max_retries_per_packet = 1 as the default retry budget.
- Inspect runtime capabilities before a real wave. Read
  references/runtime-capabilities.md when parallel, background, model override,
  completion, or workspace isolation behavior matters.
- Read references/configuration.md before mapping these policy defaults to
  project or runtime configuration. Read references/runtime-notes.md when
  current Codex lifecycle behavior matters.
- Distinguish useful parallelism during the active orchestration turn from
  autonomous background continuation. Never promise the latter unless the
  runtime explicitly guarantees it.

## Decision and execution procedure

1. **Understand.** Restate the objective, constraints, repository state, and
   what observable result would count as success.
2. **Classify.** Choose local, sequential, or delegated mode. Record why
   delegation adds value and what it costs.
3. **Preflight.** Inspect available child-spawn, nonblocking, completion,
   model/reasoning override, structured-result, and isolation capabilities.
4. **Plan.** Build a dependency graph. Mark each node's role, ownership,
   dependencies, acceptance criteria, validation, and risk. Select one ready
   wave within the worker ceiling.
5. **Specify.** Define the verification contract before spawning. Send every
   worker the packet in references/protocols.md.
6. **Spawn.** Launch all independent packets in the wave together. Give each
   write-capable worker one non-overlapping ownership domain; reviewers are
   read-only by default.
7. **Continue.** While children run, Sol performs useful non-overlapping work
   such as planning, context gathering, or integration preparation. Do not
   spawn one worker and immediately block before launching other ready work.
8. **Collect.** Wait only when a result is a critical-path dependency or the
   runtime requires an explicit collection point. Record status and evidence.
9. **Verify.** Inspect the actual diff, files, tool output, tests, sources, and
   scope. Reject unsupported claims, unrelated edits, and contradictory
   results. A passing worker report alone is insufficient.
10. **Integrate.** Accept only verified results, resolve conflicts in Sol, and
    launch the next wave only after the current wave is understood.
11. **Finish.** Run repository-level validation appropriate to the change. Sol
    alone decides DONE, reports known risks, and tells the user what remains.

## Worker roles

Roles are behavioral presets, not authorities:

- **Designer** — inspect bounded UI/UX requirements; return findings, affected
  components, proposed changes, assumptions, and ambiguities. Do not redefine
  product scope or make irreversible architecture decisions.
- **Researcher** — verify official documentation, APIs, libraries, and upstream
  behavior. Label claims FACT, INFERENCE, RECOMMENDATION, or UNKNOWN; include
  sources for external claims.
- **Fixer** — reproduce and implement a bounded correction only in assigned
  scope, then run focused validation. Do not perform unrelated cleanup.
- **Tester** — derive behavioral/regression tests from the contract, exercise
  boundary cases, and report failures plainly. Test behavior, not the Fixer's
  implementation shape.
- **Reviewer** — inspect a patch for correctness, regressions, security,
  concurrency, lifecycle, resource, and acceptance issues. Return findings and
  evidence; do not declare the whole task complete.
- **Librarian / code navigator** — locate symbols, callers, callees, tests,
  module boundaries, and dependencies, then return a compressed map. Prefer
  GitNexus, LSP, or indexes for structural questions when available and text
  search for literals, comments, configuration, and dynamic references. Read
  references/librarian.md for its evidence contract.

## Minimum worker packet

Every packet must be explicit and small:

~~~yaml
role: fixer
objective: "Fix refresh-token expiration handling"
scope:
  - src/auth/token.ts
  - src/auth/session.ts
do_not_touch:
  - database schema
  - frontend
  - unrelated formatting
context: "Refresh tokens remain usable after explicit logout."
acceptance_criteria:
  - "logout invalidates the refresh token"
  - "existing login flow remains unchanged"
validation:
  - "npm test -- auth"
  - "npm run typecheck"
ownership: "src/auth/**"
dependencies: []
output_contract:
  - summary
  - files_changed
  - tests_run
  - evidence
  - assumptions
  - unresolved_risks
~~~

Use the smallest scope that can satisfy the objective. Include forbidden scope
and ownership for every write-capable packet. If the task is broader or less
bounded than expected, return NEEDS_ORCHESTRATOR_DECISION; do not invent a
wider plan.

## Verification, failure, and state

Define these gates before execution:

- **Implementation:** the diff stays within scope and has no unrelated files.
- **Correctness:** every acceptance criterion is satisfied.
- **Validation:** the narrowest relevant tests/static checks pass, with
  regression coverage where appropriate.
- **Evidence:** each claim maps to observable code, tool output, test output,
  or cited documentation.
- **Integration:** accepted results do not conflict with other accepted work.

Use this state model for reasoning and reporting:

~~~text
UNDERSTAND -> CLASSIFY -> PLAN -> DELEGATE -> EXECUTE -> COLLECT
     ^                                               |
     |                                               v
  BLOCKED <--- NEEDS_ORCHESTRATOR_DECISION       VERIFY
     ^                         |                 /    \
     |                         +-- retry <= 1 --/      \
     +------------------------- Sol investigates       INTEGRATE
                                                          |
                                                          v
                                                FINAL_VALIDATE -> DONE
~~~

Worker statuses are only:

~~~text
DONE | NEEDS_ORCHESTRATOR_DECISION | BLOCKED
~~~

Allow at most one retry per packet with a corrected contract. After a second
failure, stop delegating that packet and investigate or implement it in Sol.
Do not spawn more workers merely to obtain consensus.

## Parallelism and write safety

- Spawn a complete wave of independent ready packets; do not serialize them by
  habit.
- Keep useful Sol work running while children execute.
- Use one writable ownership domain per worker per wave. Prefer disjoint paths.
- Make reviewers read-only. If isolation is unavailable, serialize overlapping
  edits and inspect the shared diff after every accepted change.
- Treat indexes, caches, and worker summaries as navigation evidence, not
  runtime truth. Sol must verify high-impact conclusions directly.
- If a capability is missing, fall back to fewer workers, local execution,
  read-only review, or sequential waves. Never pretend isolation, wake-up, or
  model overrides exist.

## Final Sol report

Report only verified outcomes:

~~~yaml
status: DONE | BLOCKED
work_completed: []
validation_performed: []
accepted_worker_results: []
rejected_or_retried_packets: []
known_risks: []
unresolved_items: []
~~~

The optimization target is verified useful output per unit of time, cost, and
orchestrator context—not the number of agents. Use
references/benchmarks.md before making performance claims and
references/evals.md when checking behavioral adherence to this policy.
