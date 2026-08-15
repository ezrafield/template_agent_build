# Memory: Project Facts

Type: semantic
Scope: project
Confidence: high
Last verified: 2026-08-15
Source task: .agent/tasks/README.md

## When to use

Use this memory when orienting on the template's purpose and baseline workflow.

## Content

- This repository is an agent-native project template for Codex, Claude Code, and similar coding agents.
- Agents should start with `AGENTS.md` or `CLAUDE.md`, then compile and inspect a task-specific Markdown bundle for non-trivial work.
- `.agent/tasks/` is episodic memory: task-local notes and audit trails.
- `.agent/memory/` is long-term semantic and procedural memory that must be verified before use.
- The Codex-first v0.4 catalog contains ten discoverable skills under `.agents/skills/`.
- `docs/agent/context-routes.json` is the validated route source; `INDEX.md` is its synchronized human explanation.
- Task bundles are reproducible ignored cache files under `.agent/context-cache/task-context/`, not authoritative memory.
- Active Codex hooks and command rules are machine-local opt-in files generated from `.codex/templates/`.

## Related files

- `AGENTS.md`
- `CLAUDE.md`
- `docs/agent/INDEX.md`
- `docs/agent/context-routes.json`
- `scripts/task_context.py`
- `.agent/tasks/README.md`
- `agentkit-manifest.json`
- `docs/agent/CODEX_CUSTOMIZATION.md`

## Staleness triggers

- Root agent entrypoints change.
- The context routing workflow changes.
- Task-context route schema, safety policy, or bundle format changes.
- The task-log or memory folder layout changes.
- The manifest skill catalog or guardrail activation model changes.
