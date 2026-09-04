# Luna-first decomposition

Use this reference for a non-trivial request before implementation begins. The
goal is to convert a broad objective into packets that a fast specialist can
complete and Sol can verify cheaply.

## Decomposition operators

Split a high-level task along the first useful boundary:

- **Question:** what exists, what is documented, what is risky?
- **Deliverable:** backend behavior, UI behavior, migration, tests, docs.
- **Repository domain:** separate directories, modules, services, or packages.
- **Role:** Explorer, Librarian, Oracle, Designer, Fixer, Tester, Reviewer.
- **Dependency:** work that can run now versus work that needs an earlier result.
- **Validation:** implementation, behavioral test, static review, integration.

Repeat until every packet has:

- one observable objective;
- a narrow read or write scope;
- one owner;
- explicit forbidden scope;
- acceptance criteria;
- a cheap validation path;
- no unresolved product or architecture decision.

A packet is too broad when its worker must rediscover the project plan, choose
between conflicting requirements, edit several ownership domains, or decide
whether the entire user request is complete.

## Default routing

| Lane | Route when |
| --- | --- |
| Explorer | repository shape, callers, tests, or change surface is unknown |
| Librarian | current external docs, APIs, upstream behavior, or examples matter |
| Oracle | architecture, hard debugging, risky trade-offs, or uncertainty is costly |
| Designer | users see or interact with the result |
| Fixer | implementation is understood and bounded |
| Tester | behavior can be specified independently from implementation |
| Reviewer | an actual diff exists and independent inspection can reduce risk |
| Sol | clarification, graph ownership, integration, and final acceptance |

Oracle advises; Sol decides. Explorer and Librarian gather evidence; they do not
turn findings into a new project plan.

## Example: high-level account deletion feature

The broad request:

~~~text
Add account deletion across API, persistence, UI, tests, and docs.
~~~

Becomes:

~~~text
Wave 1
  Explorer   -> map account ownership, deletion paths, and existing tests
  Librarian  -> verify external identity-provider deletion requirements
  Oracle     -> assess irreversible-data and retention trade-offs, if uncertain

Wave 2, after Sol fixes the contract
  Fixer A    -> implement backend deletion in backend/account/**
  Designer   -> implement confirmation UX in frontend/account/**
  Tester     -> derive backend/UI behavioral cases in tests/account/**

Wave 3
  Reviewer   -> inspect the combined diff read-only
  Sol        -> integrate, run repository checks, and decide completion
~~~

Do not dispatch Wave 2 before Wave 1 resolves a material contract or risk
question. Do dispatch independent Wave 1 packets together.

## Coupled work

A coupled implementation is not automatically a zero-worker task. Extract
support lanes:

- Explorer maps the path before Sol edits.
- Tester writes or specifies the behavioral contract.
- Oracle examines a risky decision.
- Reviewer checks the resulting diff.

Sol may retain the coupled edit while still delegating evidence-producing work.

## No-delegation gate

For eager mode, zero workers on non-trivial work is valid only when:

1. the user explicitly requires local execution;
2. the runtime cannot create a child;
3. after this decomposition pass, every useful lane still depends continuously
   on Sol or cannot be verified independently.

Record the concrete no-delegation reason. The following are insufficient:

- "Sol can do it";
- "the task is one feature";
- "the files are related";
- "delegation may take time";
- "each individual step looks easy".

## Packet quality check

Before dispatching, ask:

1. Can the worker finish without deciding global architecture?
2. Can Sol verify the result from a diff, test, command, or source?
3. Does the worker own one non-overlapping domain?
4. Are dependencies explicit?
5. Is the resolved model appropriate for the lane?
6. Would explaining the packet cost less than doing the work in Sol?

If the first four answers are yes, delegate. The fifth controls routing. The
sixth may keep only a truly tiny action local; it should not collapse a
multi-step request back into Sol.
