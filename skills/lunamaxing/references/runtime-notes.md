# Runtime notes

These notes preserve the assumptions behind the development thesis. They are
dated and advisory: verify current runtime behavior before relying on them.

## September 2026 check

[Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
documents project or user custom agents in `.codex/agents/*.toml` with required
`name`, `description`, and `developer_instructions`. Optional fields include
`model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and
`skills.config`. The native `[agents]` configuration has
`max_concurrent_threads_per_session`; the docs do not specify a fixed default
or guarantee queuing beyond the cap. Custom-agent file model settings can
override spawn settings. A live parent permission or sandbox override is
reapplied to a child, so generated read-only agent defaults are not an
absolute runtime guarantee.

[Codex hooks documentation](https://learn.chatgpt.com/docs/hooks) describes
`SubagentStart` and `PreToolUse`. `SubagentStart` can add context but cannot
veto a spawn. `PreToolUse` can deny some local tool calls, but hosted paths may
opt out. LunaMaxing therefore keeps strict packet validation in its explicit
helpers and does not install enforcement hooks in v0.6.

Official docs describe image input to Codex and PDF attachments, but do not
guarantee automatic propagation of those attachments to a spawned worker.
LunaMaxing does not add an Observer role until that path can be tested
reliably.

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
