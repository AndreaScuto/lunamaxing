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

Before beginning any non-trivial request, run one short decomposition pass:

1. List the concrete outputs required for completion.
2. Split them into discovery, decision, implementation, test, review, and
   integration lanes until each packet has one objective, one ownership
   boundary, and one cheap verification path.
3. Build a dependency graph: dispatch every ready, non-overlapping packet in
   the same wave; put dependent work in later waves.

Routing threshold (judgment, not quotas):

- Truly isolated, clear, low-risk action (<20 lines, 1 file) stays in Sol.
  Record a one-line no-delegation reason.
- Two or more independently ready packets run in parallel before dependent work.
- Otherwise Sol keeps only the coupled integration and still delegates any
  safe bounded support lane (Explorer map, Tester contract, Oracle check,
  Reviewer diff).

Legacy quota fields min_workers_nontrivial / target_workers_complex default to
0 and are ignored: never invent work to fill a worker count. The only ceiling
is max_workers (default 5). Zero workers on non-trivial work is valid when the
user requires local execution, the runtime cannot spawn, or no safe bounded
packet remains after decomposition.

Read references/decomposition.md for lane-splitting operators and a complete
high-level feature example.

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

- internal repository reconnaissance -> **Explorer**;
- current external documentation and library research -> Librarian;
- bounded implementation + its focused regression test -> Fixer;
- user-visible interface design and polish -> Designer.

Escalation only (not default waves):

- **Oracle** — read-only strategic advisor for risky architecture, hard
  debugging after 2+ failed attempts, or security/data-integrity decisions
  where uncertainty is expensive. Sol decides; Oracle advises.
- Reviewer — read-only diff inspection only when the diff is risky
  (security, concurrency, lifecycle, migration). Otherwise Sol reviews.
- Tester as separate lane only when behavior can be specified fully
  independently from implementation; by default the Fixer ships its own
  regression test.

If implementation is too coupled to parallelize, delegate the independent
discovery, test design, or review lane and keep only the coupled integration in
Sol.

## Dispatch efficiency, sessions, background, design

- Reference paths/lines, don't paste files (`src/auth/token.ts:42`, not full
  contents). Keep packets brief; reuse still-valid evidence.
- Reuse an available specialist session when it fits; prefer the most recently
  used matching session over a fresh spawn.
- Background discipline: launch the complete ready wave together, do only
  non-overlapping Sol work while children run, collect at terminal results,
  then reconcile. Never poll; never promise wake-up after the turn unless the
  runtime guarantees it.
- Design handoff: Designer output (layout, spacing, hierarchy, motion,
  affordances) is intentional. Sol may fix copy without changing feel; purely
  mechanical follow-up may go to Fixer, visual judgment goes back to Designer.
- File ops: <20 lines / 1 file / low-risk stays local. Multi-file or risky
  work gets explicit ownership domains.

## Runtime and model policy (optional)

Model routing is optional, not a gate. Defaults are inherit (use the running
session) unless a project .lunamaxing.json sets a concrete value.

Use scripts/configure.py to initialize, validate, or resolve
.lunamaxing.json. Explicit spawn overrides take precedence over global
subagent defaults when the runtime supports them. If a model or
reasoning_effort is unavailable, record the fallback as
requested -> effective and continue; never discard verified work over a model
mismatch. A worker's self-reported model is never evidence; runtime metadata
is authoritative but not a reason to reject an otherwise verified diff.

Example packet routing fields (optional):

~~~yaml
model: "inherit"
reasoning_effort: "inherit"
~~~

Inspect runtime capabilities before a real wave. Read
references/runtime-capabilities.md when parallel execution, completion,
overrides, or workspace isolation matters. Read references/runtime-notes.md
when current Codex lifecycle behavior matters. Extra reading is optional:
references/protocols.md, references/librarian.md, references/benchmarks.md,
references/configuration.md, references/evals.md.

## Decision and execution procedure

1. **Understand.** Restate objective, constraints, and observable DONE criteria.
2. **Decompose + Route.** Produce the short work graph; assign each lane to
   Explorer, Librarian, Fixer, Designer, Sol, or (escalation) Oracle/Reviewer.
3. **Specify.** Define acceptance + verification. Send each worker a 5-field
   packet (below).
4. **Spawn.** Launch all independent packets together with disjoint ownership.
5. **Verify + Integrate.** Inspect diff, tests, sources. Accept only verified
   results; resolve conflicts in Sol; launch the next ready wave.
6. **Finish.** Run repository-level checks. Sol alone decides DONE.

## Minimum worker packet

Every packet needs only five fields:

~~~yaml
objective: "Invalidate a refresh token during explicit logout."
scope:
  - src/auth/token.ts
do_not_touch:
  - database schema
  - frontend
acceptance_criteria:
  - "logout invalidates the refresh token"
validation:
  - "npm test -- auth"
~~~

Optional when useful: context, ownership (`src/auth/**`), dependencies: [],
read_only: true, risk, stop_conditions (return NEEDS_ORCHESTRATOR_DECISION,
do not self-expand), plus model / reasoning_effort overrides.
Use the smallest scope that satisfies the objective.

## Verification, failure, and state

Gates (proportional to risk, smallest check that proves the claim):

- **Scope:** diff stays within scope, no unrelated files.
- **Correctness:** every acceptance criterion satisfied.
- **Validation:** narrowest relevant tests/checks pass; mark not-run with
  reason instead of claiming pass.
- **Evidence:** claims map to diff, file:line, tool output, or cited source.
- **Integration:** accepted results do not conflict.

Worker statuses are only DONE | NEEDS_ORCHESTRATOR_DECISION | BLOCKED. Allow
at most one retry per packet with a corrected contract; after a second failure
Sol investigates locally. Do not spawn workers for consensus.

State shorthand: UNDERSTAND -> DECOMPOSE -> ROUTE -> EXECUTE -> COLLECT ->
VERIFY -> INTEGRATE -> DONE (plus BLOCKED / RETRY x1).

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

The target is verified useful output per unit of time, cost, and orchestrator
context — not worker count.
