---
name: lunamaxing
description: Orchestrate non-trivial coding work by decomposing high-level goals into bounded specialist tasks, routing each role to configurable models, and keeping final verification with the orchestrator. Use for multi-step work; skip only truly isolated trivial actions.
---

# LunaMaxing

LunaMaxing is a verification-first manager–worker policy:

~~~text
Sol (global context, decisions, integration)
  -> Luna workers (bounded execution and evidence)
  -> Sol (verification, integration, final acceptance)
~~~

The manager is the authority and the default scheduler, not the default
implementation worker. A worker result is a candidate plus evidence, never an
accepted fact.

## Mandatory decomposition pass

Before beginning any non-trivial request, decompose the high-level goal even
when the whole request initially looks coupled or difficult to delegate:

1. List the concrete outputs required for completion.
2. Split them into discovery, decision, implementation, test, review, and
   integration lanes.
3. Split each lane again until a packet has one objective, one ownership
   boundary, one validation path, and enough context to execute independently.
4. Route each packet to the specialist whose lane matches the work.
5. Build a dependency graph and dispatch every ready, non-overlapping packet in
   the same wave.

Do not classify the entire high-level request as "not delegatable" before this
pass. Sequential dependencies become ordered waves; they do not automatically
make every underlying task Sol work.

The default delegation mode is eager:

- A truly isolated, clear, low-risk action may stay in Sol.
- A non-trivial task should use at least min_workers_nontrivial when the runtime
  is available and one safe bounded packet exists.
- If two or more packets are independently ready, dispatch them in parallel
  before starting dependent work.
- Complex tasks should aim for target_workers_complex useful specialists, up to
  max_workers, without inventing redundant work.

If Sol keeps a non-trivial task local, state a short no-delegation reason. Valid
reasons are: the user required local execution, the runtime cannot spawn, or no
safe bounded packet remains after decomposition. "Sol can do it" is not a
valid reason.

Read references/decomposition.md for lane-splitting operators, routing rules,
and a complete high-level feature example.

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

## Direct work boundary

Sol directly handles clarification, minimal context needed to route work,
decomposition, dependency and ownership planning, spawning and tracking,
reconciliation, integration, final checks, and the user-facing decision.

Route substantive specialist work by default:

- internal repository reconnaissance -> Explorer;
- current external documentation and library research -> Librarian;
- architecture, risky trade-offs, or persistent debugging -> Oracle;
- user-visible interface design and polish -> Designer;
- bounded implementation -> Fixer;
- independent behavioral tests -> Tester;
- independent diff and regression review -> Reviewer.

If implementation is too coupled to parallelize, delegate the independent
discovery, test design, or review lane and keep only the coupled integration in
Sol. Do not keep a multi-step task entirely in Sol merely because every single
step looks easy in isolation.

## Runtime and model policy

At the start of a run, load model routing in this order:

1. packaged defaults from assets/lunamaxing.example.json;
2. project overrides from .lunamaxing.json at the current repository root;
3. explicit invocation overrides such as
   agents.oracle.model=gpt-5.6-terra or
   agents.fixer.reasoning_effort=high.

Use scripts/configure.py to initialize, validate, resolve, or inspect this
configuration. Read references/configuration.md for the complete contract.

The packaged luna-heavy defaults are:

- orchestrator: inherit the already-running session model and reasoning;
- Oracle: gpt-5.6-terra at max reasoning;
- Explorer, Librarian, Designer, Fixer, Tester, and Reviewer: gpt-5.6-luna at
  max reasoning;
- delegation: eager, minimum one worker for non-trivial work, target three for
  complex work, ceiling five.

Attach the resolved model and reasoning_effort to every worker packet and pass
them as explicit spawn overrides when the collaboration tool supports them.
Explicit spawn settings take precedence over global subagent defaults. If a
requested model or effort is unavailable, use the nearest available runtime
setting and disclose the fallback.

A skill cannot change the model of the parent session that is already running.
orchestrator.model therefore acts as a launch requirement: inherit accepts the
current session; a concrete value tells the user which model to select before
invoking LunaMaxing and can be checked when the current model is observable.

Inspect runtime capabilities before a real wave. Read
references/runtime-capabilities.md when parallel execution, completion,
overrides, or workspace isolation matters. Distinguish active parallelism from
autonomous background continuation and never promise the latter unless the
runtime guarantees it.

Read references/runtime-notes.md when current Codex lifecycle behavior matters.

## Decision and execution procedure

1. **Understand.** Restate the objective, constraints, repository state, and
   observable completion criteria.
2. **Configure.** Resolve .lunamaxing.json plus explicit overrides. Check any
   concrete orchestrator requirement and compute model/reasoning settings for
   every available role.
3. **Decompose.** Run the mandatory decomposition pass. Produce a short work
   graph with independent ready lanes and dependency-ordered later lanes.
4. **Route.** Assign each lane to Explorer, Librarian, Oracle, Designer, Fixer,
   Tester, Reviewer, or Sol using the direct work boundary above.
5. **Preflight.** Inspect child-spawn, nonblocking execution, completion,
   model/reasoning override, structured-result, and isolation capabilities.
6. **Specify.** Define acceptance and verification before spawning. Send every
   worker the packet in references/protocols.md, including resolved model and
   reasoning_effort.
7. **Spawn.** Launch all independent packets in the wave together. Give each
   writer one non-overlapping ownership domain; read-only specialists do not
   edit.
8. **Continue.** While children run, Sol performs only non-overlapping
   coordination and integration preparation. Do not immediately wait before
   launching the rest of the ready wave.
9. **Collect.** Track each child until a terminal result, then record status and
   evidence. Do not confuse silence, idle state, or a summary with completion.
10. **Verify.** Inspect the actual diff, files, tool output, tests, sources, and
    scope. Reject unsupported claims, unrelated edits, and contradictions.
11. **Integrate.** Accept only verified results, resolve conflicts in Sol, and
    launch the next dependency-ready wave.
12. **Finish.** Run repository-level validation. Sol alone decides DONE and
    reports model fallbacks, no-delegation reasons, risks, and unresolved work.

## Worker roles

Roles are configurable behavioral lanes, not authorities:

- **Oracle** — read-only strategic advisor for architecture, risky trade-offs,
  persistent debugging, security/data-integrity decisions, and high-value
  review. Use it when uncertainty is expensive; do not spend it on routine
  implementation.
- **Explorer** — read-only internal repository reconnaissance. Locate files,
  symbols, callers, tests, module boundaries, and likely change surfaces using
  GitNexus, LSP, indexes, or text search, then return compressed evidence.
- **Librarian** — read-only external knowledge retrieval for current official
  documentation, APIs, libraries, upstream issues, and examples. Label claims
  FACT, INFERENCE, RECOMMENDATION, or UNKNOWN and cite external facts.
- **Designer** — own bounded UI/UX design and related implementation: layout,
  hierarchy, interaction, responsiveness, accessibility, and visual polish.
  Do not redefine product scope.
- **Fixer** — implement a bounded, already-understood correction within assigned
  ownership and run focused validation. Do not research architecture or perform
  unrelated cleanup.
- **Tester** — derive behavioral and regression tests independently from the
  contract, exercise boundaries, and report failures plainly.
- **Reviewer** — independently inspect a patch for correctness, regressions,
  security, concurrency, lifecycle, resource, and acceptance issues. It does
  not declare the whole task complete.

The legacy Researcher role maps to Librarian. Read references/librarian.md for
the separate Explorer and Librarian evidence contracts.

## Minimum worker packet

Every packet must be explicit and small:

~~~yaml
role: fixer
model: "gpt-5.6-luna"
reasoning_effort: "max"
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
  - status
  - summary
  - model_used
  - reasoning_effort_used
  - model_fallback
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
UNDERSTAND -> CONFIGURE -> DECOMPOSE -> PLAN -> ROUTE -> DELEGATE
     ^                                                        |
     |                                                        v
  BLOCKED <--- NEEDS_ORCHESTRATOR_DECISION <- EXECUTE -> COLLECT
     ^                         |                              |
     |                         +-- retry <= configured -------v
     +------------------------- Sol investigates           VERIFY
                                                             |
                                                             v
                                                   INTEGRATE -> FINAL_VALIDATE -> DONE
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
model_routing: []
no_delegation_reason: null
known_risks: []
unresolved_items: []
~~~

The optimization target is verified useful output per unit of time, cost, and
orchestrator context—not the number of agents. Use
references/benchmarks.md before making performance claims and
references/evals.md when checking behavioral adherence to this policy.
