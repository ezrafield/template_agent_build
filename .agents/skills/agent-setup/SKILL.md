---
name: agent-setup
description: Bootstrap or audit this agent kit after installation. Use when project commands, stack context, module cards, or agent validation are missing or stale; do not use for normal feature implementation.
---

# Agent Setup

1. Run `python scripts/agent_setup.py` from the repository root.
2. Review the detected stack and `docs/agent/COMMANDS.md` instead of accepting placeholders blindly.
3. Fill unresolved project-specific TODOs in the codemap and module cards.
4. Run `python scripts/agentkit_installer.py check --source . --target .`.
5. Smoke-test task context with `python scripts/task_context.py build "audit agent kit setup" --route agent-setup --no-search`.
6. Run `make validate-agent-assets`, `make check-context-staleness`, and `make audit-module-cards`.
7. Report detected commands, generated context, validation failures, and remaining TODOs.

Preserve existing project instructions and user-owned context. Do not overwrite active guardrails, project memory, or application files during setup.
