# LunaMaxing

![LunaMaxing logo](assets/lunamax.png)

Verification-first manager–worker orchestration for Codex.

LunaMaxing helps **Sol**, the orchestrator, split independent work into bounded **Luna** worker tasks and verify every result before integration.

## Use

Install the plugin, then invoke the skill with:

```text
$lunamaxing
```

Use it when work can be decomposed into independent, low-coupling tasks. Keep tightly coupled, ambiguous, or trivial work with Sol.

## Core principles

- Sol owns planning, architecture, integration, and final acceptance.
- Workers receive explicit scope, acceptance criteria, and validation commands.
- Worker output is evidence to verify, never an automatic fact.
- Parallelism is bounded and used only when it adds value.
- Every accepted change is checked against the actual diff and repository tests.

## Plugin structure

```text
lunamaxing/
├── .codex-plugin/plugin.json
├── assets/lunamax.png
└── skills/lunamaxing/
    ├── SKILL.md
    └── agents/openai.yaml
```

LunaMaxing is packaged as a skills-only plugin; no MCP server is required.
