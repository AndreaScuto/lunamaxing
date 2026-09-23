# Changelog

## 0.5.0 — 2026-09-23

- Replaced eager worker quotas with a judgment threshold: trivial work stays in Sol, parallel waves need two or more independent lanes.
- Changed defaults to balanced delegation with zero minimum workers and inherit model routing (Oracle stays Terra/max for escalation).
- Demoted Oracle and Reviewer to escalation-only lanes; Fixer ships its own regression test by default.
- Slimmed worker packets to five required fields with optional routing, and replaced model-mismatch rejection with recorded fallback.

- Added documented GPT-6 Astra routing for the orchestrator and every worker role.
- Made concrete worker model and reasoning overrides mandatory at spawn time.
- Added runtime model mismatch rejection and auditable role-prefixed task names.
- Stopped treating worker self-reported role/model labels as routing evidence.

## 0.3.1 — 2026-09-04

- Changed the default Oracle routing to gpt-5.6-terra with max reasoning.

## 0.3.0 — 2026-09-04

- Added project-local .lunamaxing.json model and reasoning configuration.
- Added explicit per-role spawn routing with Oracle on Terra and specialist lanes on Luna by default.
- Added configurable orchestrator requirements while preserving the current parent-session limitation.
- Added Oracle and Explorer lanes and separated internal exploration from external research.
- Made decomposition mandatory before retaining non-trivial work in Sol.
- Added eager delegation thresholds and explicit no-delegation reasons.
- Added model-routing evidence to worker packets, results, and final reports.
- Added delegation-rate and effective-model fields to benchmark records.
