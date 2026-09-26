"""Canonical LunaMaxing specialist roles and write permissions."""

AGENT_ROLES = (
    "oracle",
    "explorer",
    "librarian",
    "designer",
    "fixer",
    "tester",
    "reviewer",
)
ROLE_ALIASES = {"researcher": "librarian"}
ROLE_REGISTRY = {
    "oracle": {
        "may_write": False,
        "default_read_only": True,
        "description": "Give an independent technical judgment grounded in evidence.",
        "developer_instructions": "Inspect relevant evidence and compare options. Do not modify files; report findings, evidence, and risks.",
    },
    "explorer": {
        "may_write": False,
        "default_read_only": True,
        "description": "Map the relevant code and trace behavior through the project.",
        "developer_instructions": "Inspect the assigned area and trace callers and data flow. Do not modify files; report paths, behavior, and findings.",
    },
    "librarian": {
        "may_write": False,
        "default_read_only": True,
        "description": "Research assigned questions and provide sourced findings.",
        "developer_instructions": "Use authoritative sources for external claims. Do not modify files; separate facts, inferences, recommendations, and unknowns.",
    },
    "designer": {
        "may_write": True,
        "default_read_only": False,
        "description": "Turn the assigned requirements into a bounded implementation design.",
        "developer_instructions": "Stay within the assigned scope and ownership. Make the smallest useful change and report decisions, evidence, and risks.",
    },
    "fixer": {
        "may_write": True,
        "default_read_only": False,
        "description": "Implement the assigned bounded code change.",
        "developer_instructions": "Fix the root cause within the assigned scope and ownership. Run the requested checks and report changed files, evidence, and risks.",
    },
    "tester": {
        "may_write": True,
        "default_read_only": True,
        "description": "Check the assigned behavior with focused tests.",
        "developer_instructions": "Verify the assigned criteria. If authorized to write, change test-owned files only; never modify production code.",
    },
    "reviewer": {
        "may_write": False,
        "default_read_only": True,
        "description": "Review the assigned change for correctness and missing coverage.",
        "developer_instructions": "Inspect the diff and evidence. Do not modify files; report only actionable findings with severity and locations.",
    },
}


def canonical_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role) if isinstance(role, str) else ""
