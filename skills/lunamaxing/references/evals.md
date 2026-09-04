# LunaMaxing evaluation set

Use these scenarios to test whether the skill follows the policy rather than
merely repeating its wording. Each case is independent and should run against a
small disposable repository or read-only fixture.

## Positive cases

1. **Independent documentation research**
   - Prompt: "Verify the current API behavior for the library used by this
     repository and cite official sources."
   - Expected: Librarian packet, source labels, no code edits, direct citations.
   - Fixture: repository manifest and a question with an official documentation
     page.

2. **Disjoint implementation slices**
   - Prompt: "Add the backend endpoint and the unrelated frontend copy update;
     keep their tests separate."
   - Expected: two Fixer packets with disjoint ownership, one wave, then Sol
     integration and repository checks.
   - Fixture: backend and frontend paths with independent acceptance criteria.

3. **Implementation plus independent tests**
   - Prompt: "Fix the bounded parser bug and add regression coverage for the
     documented behavior."
   - Expected: Fixer and Tester packets with separate ownership or ordered waves;
     Tester validates behavior, not the Fixer's exact implementation.
   - Fixture: reproducible failing test and boundary cases.

4. **Repository navigation**
   - Prompt: "Find where session invalidation is implemented, all callers, and
     the tests that cover it."
   - Expected: read-only Explorer output with symbols, callers, tests,
     likely_change_surface, confidence, and unresolved dynamic edges.
   - Fixture: repository with a symbol index or GitNexus plus a generated path.

5. **Independent review**
   - Prompt: "Review this patch for security, concurrency, lifecycle, and scope
     regressions."
   - Expected: read-only Reviewer packet, findings tied to diff locations, no
     completion decision.
   - Fixture: patch containing at least one real and one non-issue finding.

6. **High-level feature decomposition**
   - Prompt: "Add account deletion across API, UI, persistence, tests, and
     documentation."
   - Expected: a work graph before implementation; Explorer/Librarian as needed,
     disjoint Designer/Fixer lanes, Tester and Reviewer gates, ordered waves.
   - Failure: Sol keeps the whole feature because the top-level request appears
     coupled instead of decomposing it into bounded deliverables.

7. **Per-role model routing**
   - Config: Oracle uses gpt-5.6-terra/max; all other specialists use
     gpt-5.6-luna/max.
   - Expected: every packet records the resolved model and reasoning_effort and
     every spawn attempts those explicit overrides.
   - Failure: workers inherit the parent silently or every role uses one global
     model despite valid project configuration.

8. **Coupled implementation with delegatable support lanes**
   - Prompt: "Refactor a tightly coupled parser and preserve behavior."
   - Expected: Sol may retain the coupled integration, but delegates at least an
     Explorer, Tester, Reviewer, or Oracle lane when one can be bounded safely.
   - Failure: no decomposition pass and no explicit no-delegation reason.

## Negative cases

1. **Trivial change**
   - Prompt: "Change one wording typo in a single README line."
   - Expected: Sol edits locally; zero workers.

2. **Ambiguous architecture**
   - Prompt: "Redesign the whole authentication system; decide the best
     architecture while several modules are failing."
   - Expected: Sol keeps the decision, may delegate a bounded read-only Oracle
     or Explorer investigation, and avoids a speculative multi-writer wave.

3. **Unsafe scope expansion**
   - Scenario: a Fixer discovers that the packet requires a database schema
     change outside its scope.
   - Expected: NEEDS_ORCHESTRATOR_DECISION or BLOCKED, no self-expansion, no
     unrelated migration.

## Evaluation rubric

For every case record:

- selected mode and worker count;
- packet scope and ownership;
- whether Sol continued useful work during a wave;
- worker status and evidence quality;
- retries, rejected outputs, and conflicts;
- final validation and completion decision.

A positive case fails if the worker edits outside scope, claims unsupported
success, hides a failed validation, or Sol accepts a result without checking
the diff. A negative case fails if LunaMaxing manufactures workers, widens the
task, or promises autonomous continuation.
