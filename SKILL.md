---
name: lunamaxing
description: Orchestrate decomposable coding work with a strong manager and bounded parallel workers, using native Codex multi-agent tools and explicit evidence gates. Use when subtasks are independently verifiable; skip trivial, tightly coupled, or purely sequential work.
---

# LunaMaxing

Use a manager-worker shape without building a swarm:

    Sol (plan, decisions, integration) -> Luna workers (bounded execution) -> Sol (verification, final acceptance)

The manager is the authority. A worker result is a candidate plus evidence, never an accepted fact.

## Operating rules

- Keep repository-wide context, decomposition, architecture, prioritization, ambiguity, conflict resolution, integration, risk management, and the final completion decision in Sol (or the strongest available orchestrator).
- Prefer the strongest available orchestrator at high/xhigh reasoning. Prefer Luna at maximum reasoning for narrow worker packets when those model/reasoning overrides are supported; otherwise use the runtime's available settings without pretending an override exists.
- Workers execute; they do not plan the whole task, recursively spawn workers, negotiate with one another, or expand scope.
- Treat max_workers = 5 as a ceiling, not a target. Use 0..min(independent_ready_tasks, configured_ceiling, runtime_limit) workers.
- Parallelize only bounded, low-coupling, verifiable, context-light, recoverable work. Keep global judgment, unresolved architecture, and tightly coupled edits in Sol.
- Consensus is not verification. Agent count is not a confidence metric.
- Define acceptance and verification before spawning. Sol alone decides whether the complete task is done.

## Classify before delegating

1. Trivial or one-file work: do it locally.
2. Sequential, highly coupled, high-risk, or ambiguous work: keep it in Sol, or delegate only a narrow investigation.
3. Decomposable work: build a dependency graph, identify the ready wave, and delegate only independent nodes.

If a worker discovers that its packet is broader or less bounded than expected, it must return NEEDS_ORCHESTRATOR_DECISION rather than inventing a wider plan.

## Worker roles

Roles are behavioral presets, not authorities:

- Designer — inspect bounded UI/UX requirements and return findings, affected components, proposed changes, assumptions, and ambiguities. Do not redefine product scope or make irreversible architecture decisions.
- Researcher — verify official documentation, APIs, library behavior, and upstream issues. Label each claim FACT, INFERENCE, RECOMMENDATION, or UNKNOWN; include sources for external claims.
- Fixer — reproduce and implement a bounded correction only within assigned files/scope, then run focused validation. Do not perform unrelated cleanup.
- Tester — derive behavioral/regression tests from the contract, exercise boundary cases, and report failures plainly. Test behavior, not the Fixer's implementation shape.
- Reviewer — inspect a patch for correctness, regressions, security, concurrency, lifecycle, resource, and acceptance-criteria issues. Return findings and evidence; do not declare the whole task complete.
- Librarian / code navigator — locate symbols, callers, callees, tests, module boundaries, and dependencies; return a compact map. Use GitNexus, LSP, or indexes for structural questions when available and textual search for literals, comments, configuration, and dynamic references. An index is navigation evidence, not runtime truth.

## Task packet

Send every worker a compact, explicit packet containing:

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
    output_contract:
      - summary
      - files_changed
      - tests_run
      - evidence
      - assumptions
      - unresolved_risks

Use the smallest scope that can satisfy the objective. Include ownership and forbidden scope for write-capable work.

## Waves and write ownership

1. Inspect runtime capabilities: parallel spawn, nonblocking child execution, completion notification, per-child model/reasoning overrides, and isolated worktrees.
2. Spawn one complete wave of independent packets. Do not spawn a worker and immediately block for it before launching other independent work.
3. Continue useful, non-overlapping Sol work while workers run.
4. Collect results when they become critical-path dependencies, then verify before launching the next wave.
5. Assign one writable ownership domain per worker per wave. Prefer disjoint paths; make reviewers read-only. If isolation is unavailable, serialize overlapping edits and inspect the shared diff after each accepted change.

Do not build a scheduler or promise autonomous post-turn continuation. Background completion and wake-up behavior are runtime-dependent; when a capability is missing, use a safe fallback such as fewer workers, local execution, read-only review, or sequential waves.

## Verification gate

For each packet, define before execution:

- implementation: the diff stays within scope and contains no unrelated files;
- correctness: every acceptance criterion is satisfied;
- tests/static checks: the narrowest relevant commands pass, plus regression coverage where appropriate;
- evidence: each claim maps to observable code, tool output, test output, or cited documentation;
- integration: accepted results do not conflict with other accepted results.

After collection, Sol must inspect the actual diff and evidence, run repository-level validation appropriate to the change, reject unsupported claims, and resolve contradictions. A passing worker report alone is insufficient.

Allow at most one retry per packet with a corrected contract. After a second failure, stop delegating that packet and investigate or implement it in Sol. Do not spawn more workers merely to obtain consensus.

Worker output should be concise and structured:

    status: DONE | NEEDS_ORCHESTRATOR_DECISION | BLOCKED
    summary: "..."
    files_changed: []
    tests_run:
      - command: "..."
        result: "pass/fail/not-run"
    evidence: []
    assumptions: []
    unresolved_risks: []

## Execution algorithm

1. Understand the user's objective and repository constraints.
2. Classify the task and decide whether delegation adds more value than its orchestration tax.
3. Build the dependency graph and choose a ready wave within the worker ceiling.
4. Write strict packets with acceptance and verification contracts.
5. Spawn independent workers using native Codex collaboration tools.
6. Keep doing non-overlapping Sol work; collect only when needed.
7. Verify evidence and scope, retry once when useful, and reject unsupported output.
8. Integrate accepted changes, run final repository-level checks, and make the completion decision in Sol.
9. Report work completed, validation performed, retries/rejections, known risks, and unresolved items.

The optimization target is verified useful output per unit of time, cost, and orchestrator context—not the number of agents. Measure those trade-offs before claiming that LunaMaxing improves a task category.
