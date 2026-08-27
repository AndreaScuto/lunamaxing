# LunaMaxing protocols

Use this reference when Sol delegates a packet, reviews a worker result, or
needs to explain why a result was accepted or rejected. The protocol keeps
worker contexts narrow while leaving global judgment with Sol.

## Packet contract

A packet is complete only when it answers these questions:

| Field | Required | Meaning |
| --- | --- | --- |
| role | yes | One of designer, researcher, fixer, tester, reviewer, librarian |
| objective | yes | One observable outcome, not a general project goal |
| scope | yes | Files, symbols, or read-only search boundary |
| do_not_touch | yes | Explicit forbidden paths, systems, and cleanup |
| context | yes | The minimum facts needed to work safely |
| acceptance_criteria | yes | Observable conditions for success |
| validation | yes | Commands, checks, sources, or fixtures to inspect |
| ownership | write work | The single writable domain owned by this worker |
| dependencies | yes | Packet IDs or prerequisites; use [] when none |
| output_contract | yes | Fields the worker must return |

Optional fields can make a packet safer:

- risk: low, medium, or high, with one sentence explaining why;
- read_only: true for research, librarian, tester, or reviewer work that must
  not edit files;
- tool_budget: a practical ceiling for searches, commands, or retries;
- expected_files: likely paths without turning them into permission to expand;
- stop_conditions: conditions that require BLOCKED or
  NEEDS_ORCHESTRATOR_DECISION.

A good objective is narrow enough that a reviewer can decide pass/fail without
reconstructing the whole project.

## Recommended packet

~~~yaml
id: auth-refresh-fix
role: fixer
objective: "Invalidate a refresh token during explicit logout."
scope:
  - src/auth/token.ts
  - src/auth/logout.ts
do_not_touch:
  - database schema
  - frontend
  - unrelated formatting
context: "Logout currently leaves the refresh token usable."
acceptance_criteria:
  - "logout invalidates the refresh token"
  - "existing login flow remains unchanged"
  - "a regression test covers the invalidation"
validation:
  - "npm test -- auth"
  - "npm run typecheck"
ownership: "src/auth/**"
dependencies: []
read_only: false
risk: medium
stop_conditions:
  - "required behavior depends on a schema change"
output_contract:
  - status
  - summary
  - files_changed
  - tests_run
  - evidence
  - assumptions
  - unresolved_risks
~~~

Before spawning, Sol checks that scope and ownership do not overlap with other
write-capable packets in the same wave. If they do, split the domain or put the
packets in different waves.

## Worker output contract

Workers return concise structured output:

~~~yaml
status: DONE | NEEDS_ORCHESTRATOR_DECISION | BLOCKED
summary: "One sentence describing the result."
files_changed:
  - src/auth/token.ts
tests_run:
  - command: "npm test -- auth"
    result: pass | fail | not-run
    notes: "Optional boundary or environment detail."
evidence:
  - kind: code | test | command | source | diff
    claim: "The refresh token is revoked before logout returns."
    location: "src/auth/token.ts:42"
    strength: direct | corroborating | insufficient
assumptions:
  - "The existing repository token store is authoritative."
unresolved_risks:
  - "No multi-device integration fixture exists."
~~~

Rules:

- DONE requires evidence and a scope check; a summary alone is not enough.
- NEEDS_ORCHESTRATOR_DECISION means the packet boundary, requirement, or
  dependency is invalid or ambiguous. It is not a request to self-expand.
- BLOCKED means the worker cannot continue without an external state change,
  missing fixture, unavailable capability, or Sol decision.
- files_changed must be [] for read-only packets.
- tests_run must state not-run and why when validation could not execute.
- Research claims label their type as FACT, INFERENCE, RECOMMENDATION, or
  UNKNOWN and include a source for external facts.
- Reviewers report findings with severity and evidence; they never grant final
  completion.

## Evidence standard

Use the strongest evidence available:

1. **Direct:** the actual diff, file content, command output, test result, or
   authoritative source directly supports the claim.
2. **Corroborating:** an independent result supports the claim but does not
   cover every acceptance criterion.
3. **Insufficient:** a worker assertion, stale index, intuition, or consensus
   without an observable artifact.

Sol accepts a criterion only when its evidence is direct or when multiple
independent corroborating artifacts leave no material uncertainty. A passing
test that does not exercise the criterion is not evidence for that criterion.

## Verification contract

Define this before execution and evaluate it after collection:

~~~yaml
verification_contract:
  implementation:
    - "diff stays within assigned scope"
    - "no unrelated files changed"
  correctness:
    - "every acceptance criterion is satisfied"
  validation:
    - "narrowest relevant suite passes"
    - "static checks pass where relevant"
  evidence:
    - "claims map to observable artifacts"
    - "external claims have sources"
  integration:
    - "accepted results do not conflict"
    - "repository-level checks still pass"
~~~

Sol must inspect the actual working tree, not only the worker's reported
files. If the worker edited outside scope, reject or repair in Sol before
integration.

## State transitions

Use these states for a packet or wave:

| State | Enter when | Exit to |
| --- | --- | --- |
| UNDERSTAND | objective and constraints are being gathered | CLASSIFY |
| CLASSIFY | local/sequential/delegated choice is made | PLAN |
| PLAN | graph, ownership, and gates are defined | DELEGATE |
| DELEGATE | packets are complete and ready | EXECUTE |
| EXECUTE | workers are running | COLLECT, BLOCKED, NEEDS_ORCHESTRATOR_DECISION |
| COLLECT | worker output is available | VERIFY |
| VERIFY | evidence and diff are inspected | INTEGRATE, RETRY, BLOCKED |
| RETRY | one corrected packet is being attempted | EXECUTE, BLOCKED |
| INTEGRATE | accepted changes are reconciled | PLAN, FINAL_VALIDATE |
| FINAL_VALIDATE | repository-level checks run | DONE, BLOCKED |

"DONE" is a Sol decision, never a worker status. Any contradiction in accepted
evidence returns the affected packet to VERIFY. A second failure after one
retry exits delegation for that packet and moves the investigation to Sol.

## Retry and escalation

Default budget: one retry per packet.

Retry only when Sol can name a corrected contract, such as a missing file,
unclear acceptance criterion, invalid command, or accidental scope collision.
Do not retry merely to obtain a more reassuring explanation.

Escalate immediately when:

- the task needs an architecture decision;
- a worker discovers cross-domain writes;
- acceptance criteria conflict;
- required evidence is unavailable;
- a worker reports a security, data-loss, or destructive risk;
- the runtime cannot provide a safe execution strategy.

A worker must not spawn a verifier or planner. Sol may run one independent
read-only verification pass, but still owns the final decision.

## Write ownership

Represent ownership as a path or symbol domain, for example:

~~~yaml
ownership:
  writable:
    - backend/auth/**
  read_only:
    - frontend/**
    - tests/**
~~~

For each wave:

- no two write domains may include the same path or symbol;
- a reviewer/tester may read a writer's domain but not edit it;
- overlapping changes move to sequential waves;
- when no isolated worktree exists, Sol inspects the shared diff after each
  accepted result;
- generated files count as owned paths if a command writes them.

If a conflict appears, stop the affected packet, preserve evidence, and let Sol
resolve the integration order. Do not merge by last-write-wins.

## Machine checks

The dependency-free helpers in scripts/ make the protocol auditable without
pretending to run workers:

~~~text
python scripts/check_packet.py packet.json --kind packet
python scripts/check_packet.py result.json --kind result --packet packet.json
python scripts/check_wave.py wave.json --max-workers 5
python scripts/check_state_log.py state-log.json
~~~

A wave file is either a JSON array of packets or an object with a wave array:

~~~json
{
  "wave": [
    {"id": "backend", "role": "fixer", "ownership": "backend/**"},
    {"id": "frontend", "role": "fixer", "ownership": "frontend/**"}
  ]
}
~~~

The wave checker rejects missing packet fields, duplicate IDs, same-wave
dependencies, worker counts above the ceiling, and overlapping writable
ownership. Read-only packets do not create write conflicts.

A state-log file contains a states array and may set max_retries:

~~~json
{
  "max_retries": 1,
  "states": ["UNDERSTAND", "CLASSIFY", "PLAN", "FINAL_VALIDATE", "DONE"]
}
~~~

The state checker verifies legal transitions, a terminal end state, and the
retry budget. It is a guardrail for Sol, not an autonomous scheduler.

## Sol completion report

~~~yaml
status: DONE | BLOCKED
work_completed:
  - "..."
validation_performed:
  - command: "..."
    result: pass | fail | not-run
accepted_worker_results:
  - packet_id: auth-refresh-fix
    evidence: ["src/auth/token.ts:42", "npm test -- auth"]
rejected_or_retried_packets: []
known_risks: []
unresolved_items: []
~~~

This report is the handoff boundary to the user. It should state what was
verified, what was not, and why the final decision is safe.
