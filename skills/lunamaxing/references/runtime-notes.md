# Runtime notes

These notes preserve the assumptions behind the development thesis. They are
dated and advisory: verify current runtime behavior before relying on them.

## August 2026 baseline

The intended native shape is:

- Sol can spawn bounded child agents for well-scoped tasks;
- independent packets can run in parallel;
- Sol can perform non-overlapping work while children run;
- concurrency, model overrides, completion behavior, and workspace isolation
  are runtime capabilities rather than promises made by the skill.

Known areas to re-check when the runtime changes:

- background completion and wake-up after the foreground turn;
- child worktree or working-directory isolation;
- MultiAgentV2 concurrency and lifecycle behavior;
- per-child model and reasoning overrides.

Useful primary references:

- [Codex multi-agent handler](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/multi_agents_spec.rs)
- [Codex experimental multi-agent prompt](https://github.com/openai/codex/blob/main/codex-rs/core/templates/collab/experimental_prompt.md)
- [Parallel/background lifecycle discussion](https://github.com/openai/codex/issues/22099)
- [Background completion/wake-up limitation](https://github.com/openai/codex/issues/15723)
- [Per-subagent working-directory isolation](https://github.com/openai/codex/issues/18969)
- [MultiAgentV2 concurrency discussion](https://github.com/openai/codex/issues/40211)

## Safe interpretation

These references do not justify an autonomous scheduler. LunaMaxing should
continue to distinguish active parallel orchestration from fully autonomous
background continuation. If a capability is unclear or unavailable, use the
fallbacks in runtime-capabilities.md and disclose the limitation.
