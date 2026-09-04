# Changelog

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
