# Explorer and Librarian contracts

Explorer keeps repository-search noise out of Sol's strategic context.
Librarian keeps external documentation and library research out of it. Both
return compressed evidence and never redesign, prioritize, approve, or edit.

## Explorer: ask a precise repository question

Good questions have a bounded answer:

- Where is symbol X defined and used?
- Which callers reach handler Y?
- What modules depend on service Z?
- Which tests exercise this behavior?
- What is the likely change surface for objective Q?
- Which path reaches this error or data sink?

Bad questions ask Explorer to own architecture, choose between user
intentions, or explore the entire repository without a stopping condition.

## Choose the lookup tool

Classify the question before searching:

| Question shape | Preferred tool |
| --- | --- |
| symbol definition, callers, callees, dependency graph, control/data path | GitNexus, LSP, or a repository index when available |
| error text, configuration key, comment, documentation, literal value | textual search |
| dynamic import, generated code, reflection, unresolved index result | textual search plus direct file inspection |
| high-impact behavior | structural lookup followed by direct source/test verification |

Tool selectivity matters. GitNexus is not a replacement for text search, and
an index is not runtime truth.

## Compact evidence output

Return only the structural facts Sol needs:

~~~yaml
role: explorer
question: "Where is refresh-token invalidation implemented and what depends on it?"
evidence:
  primary_symbols:
    - symbol: revokeRefreshToken
      file: src/auth/token.ts
      responsibility: "invalidates persisted refresh tokens"
  callers:
    - file: src/auth/logout.ts
      symbol: logout
  callees:
    - file: src/auth/token.ts
      symbol: TokenRepository.revoke
  downstream_dependencies:
    - SessionService
    - TokenRepository
  related_tests:
    - tests/auth/logout.test.ts
    - tests/auth/token.test.ts
  likely_change_surface:
    - src/auth/token.ts
    - src/auth/logout.ts
  confidence: high
  unresolved:
    - "No multi-device integration test found."
~~~

Every important item should have a file, symbol, line, query, or command that
Sol can inspect. Compress repeated search output into counts and paths rather
than dumping raw results.

## Evidence and confidence

Use confidence to describe lookup completeness, not correctness:

- high: definitions, callers, and relevant tests were directly inspected;
- medium: the index or search found the likely path but a dynamic edge remains;
- low: the result depends on generated, reflective, stale, or incomplete data.

Always list unresolved dynamic behavior. For high-impact changes, Sol verifies
the source and runtime behavior directly even when confidence is high.

The rule is:

~~~text
index result != runtime truth
worker summary != accepted design
~~~

## Librarian: external knowledge retrieval

Use Librarian for current official documentation, version-specific API
behavior, upstream issues, examples, and established workarounds. Do not use it
for repository symbol traversal; that belongs to Explorer.

Return:

~~~yaml
role: librarian
question: "Does library version X support refresh-token revocation?"
claims:
  - type: FACT
    statement: "..."
    source: "https://official.example/docs/..."
  - type: INFERENCE
    statement: "The repository likely needs ..."
sources:
  - title: "Official API reference"
    url: "https://official.example/docs/..."
version_scope: "library X.Y"
confidence: high
unresolved:
  - "The upstream issue does not cover the repository's adapter."
~~~

Label every claim FACT, INFERENCE, RECOMMENDATION, or UNKNOWN. Prefer primary
and official sources, distinguish publication date from event/version date, and
keep quotations short. Sol decides whether the external evidence applies to the
local implementation.

## Read-only boundary

Explorer and Librarian are read-only. They must not modify code, format files,
update indexes as a side effect, or turn a finding into an architecture
decision.

## Returning control to Sol

Explorer ends with:

- likely change surface;
- affected tests;
- assumptions;
- unresolved risks;
- one recommended next question, if needed.

Librarian ends with:

- version and date scope;
- official sources;
- claim labels;
- applicability assumptions;
- unresolved external uncertainty.

Do not return a new project plan. Sol owns the dependency graph and decides
whether another worker or a local inspection is warranted.
