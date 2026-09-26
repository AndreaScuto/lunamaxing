---
name: lunamaxing
description: Orchestrate non-trivial coding work by decomposing high-level goals into bounded specialist tasks, routing each role to configurable models, and keeping final verification with the orchestrator. Use for multi-step work; skip only truly isolated trivial actions.
---

# LunaMaxing

LunaMaxing is a verification-first manager–worker policy:

~~~text
Sol (global context, decisions, integration)
  -> configured specialist workers (bounded execution and evidence)
  -> Sol (verification, integration, final acceptance)
~~~

The manager is the authority and the default scheduler, not the default
implementation worker. A worker result is a candidate plus evidence, never an
accepted fact.

## Mandatory decomposition pass

Before beginning any non-trivial request, run one short decomposition pass:

1. List the concrete outputs required for completion.
2. Split them by question, module, file ownership, implementation slice, test,
   or review concern. Repeat while each piece can be executed and verified
   independently at lower total coordination cost.
3. Give each packet one objective, bounded scope, explicit exclusions, an
   owner, acceptance criteria, and cheap validation. Keep architecture and
   coupled integration with Sol.
4. Dispatch every useful ready packet with non-overlapping write ownership;
   put dependent work in later waves. Codex controls actual runtime capacity.

Routing threshold (judgment, not quotas):

- A truly isolated, clear, low-risk action may stay in Sol. Record a one-line
  no-delegation reason for non-trivial work kept local.
- Two or more independently ready packets run in parallel before dependent work.
- Otherwise Sol keeps only the coupled integration and still delegates any
  safe bounded support lane (Explorer map, Tester contract, Oracle check,
  Reviewer diff).

Never invent work to fill a worker count. There is no LunaMaxing default
ceiling; `delegation.max_workers` is only an optional explicit user limit.
Respect native Codex capacity and write safety without building a queue or
scheduler. Zero workers on non-trivial work is valid when the user requires
local execution, the runtime cannot spawn, or no safe bounded packet remains.

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
- `scripts/roles.py` is the canonical specialist registry. Oracle, Explorer,
  Librarian, and Reviewer are always read-only. Tester is read-only by default
  and may write only in an explicitly owned test scope. Fixer and Designer may
  write when their packet declares non-empty ownership.

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
- Reuse an available specialist session only for the same role and repository
  area while its context remains useful and uncontaminated.
- Background discipline: launch the complete ready wave together, do only
  non-overlapping Sol work while children run, collect at terminal results,
  then reconcile. Never poll; never promise wake-up after the turn unless the
  runtime guarantees it.
- Design handoff: Designer output (layout, spacing, hierarchy, motion,
  affordances) is intentional. Sol may fix copy without changing feel; purely
  mechanical follow-up may go to Fixer, visual judgment goes back to Designer.
- A local edit is a judgment call; every writable worker gets an explicit
  ownership domain.

## Runtime and model policy (optional)

Model routing is optional, not a gate. Defaults are inherit (use the running
session) unless a project .lunamaxing.json sets a concrete value.

Use `scripts/configure.py interactive .lunamaxing.json` to create or edit model
settings, or use init/validate/resolve for scripting. Explicit spawn overrides
take precedence over global
subagent defaults when the runtime supports them. If a model or
reasoning_effort is unavailable, record the fallback as
requested -> effective and continue; never discard verified work over a model
mismatch. A worker's self-reported model is never evidence; runtime metadata
is authoritative but not a reason to reject an otherwise verified diff.
Project `.codex/agents/*.toml` role files may override spawn settings; check
for stale generated files before claiming a routing override took effect.

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

Optional `scripts/generate_agents.py` creates native Codex specialist files
from the canonical registry when requested. LunaMaxing also works without
generated agent files.

## Decision and execution procedure

1. **Understand.** Restate objective, constraints, and observable DONE criteria.
2. **Decompose + Route.** Produce the short work graph; assign each lane to
   Explorer, Librarian, Fixer, Designer, Sol, or (escalation) Oracle/Reviewer.
3. **Specify.** Define acceptance + verification. Send each worker a compact
   packet (below).
4. **Spawn.** Launch all independent packets together with disjoint ownership.
5. **Verify + Integrate.** Inspect diff, tests, sources. Accept only verified
   results; resolve conflicts in Sol; launch the next ready wave.
6. **Finish.** Run repository-level checks. Sol alone decides DONE.

## Minimum worker packet

Every packet needs these compact fields:

~~~yaml
role: fixer
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
ownership: "src/auth/**"
~~~

Ownership is required for writable packets; omit it for read-only packets.
Optional when useful: context, dependencies: [],
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
- **Repository state:** `scripts/check_git.py` compares actual changed paths
  with packet scope, ownership, and exclusions when Git is available.
- **Integration:** accepted results do not conflict.

Worker statuses are only DONE | NEEDS_ORCHESTRATOR_DECISION | BLOCKED. DONE
without relevant evidence is invalid. Allow at most one retry per packet only
with a corrected contract; raise reasoning effort when available. After a
second failure Sol investigates or asks Oracle for a bounded read-only check.
Do not spawn workers for consensus.

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
