# AGENTS.md

## Project Purpose

This repository is an agent-native project template for Codex, Claude Code, and similar coding agents. It demonstrates progressive context loading, discoverable skills, deterministic validation, and lightweight project memory.

## Instruction Hierarchy

- Read this file before non-trivial work, then route through `docs/agent/INDEX.md`.
- Codex loads at most one instruction file per directory from the repository root to the working directory. At one level, `AGENTS.override.md` is preferred over `AGENTS.md`; ancestors remain active.
- Use a root `AGENTS.override.md` only as a temporary local replacement. Use nested instructions for durable directory-specific guidance.
- Project instructions and skills do not override system, managed, safety, or explicit user constraints.

## Plan Evolution Rule

- Before executing any explicit plan, roadmap, strategy change, migration, or version upgrade—or whenever work is organized as a multi-step plan—use `$plan-evolution` and create or update its Markdown record under `.agent/plans/`.
- Treat chat or tool plans as transient. Keep the file current with the goal, strategy hypothesis, success signals, decisions, outcome evidence, and separate learning for the user and AI process; move closed records to `completed/`.
- Create one linked record for every material version upgrade. Read-only answers and unplanned one-step actions are exempt. Store concise rationale, never secrets, private data, or hidden chain-of-thought.

## Default Workflow

1. Understand the task and keep its scope explicit.
2. Read `docs/agent/INDEX.md` and only the context it routes to.
3. Check `.agent/memory/index.json` for relevant guidance, then verify it against current files.
4. Use targeted retrieval before full-file reads: semantic search when useful, `rg` for exact confirmation, and symbol tooling only when references or safe refactors require it.
5. Before editing, identify the selected files, why they matter, and the main uncertainty or risk.
6. Make the smallest safe change and update tests or docs when behavior changes.
7. Run targeted checks before broader checks.
8. Report changed files, commands run, and remaining risks.

## Context Rules

- Do not scan the whole repository unless the task requires it.
- Prefer module cards, targeted reads, and deterministic scripts over broad context loading.
- Treat memory and generated knowledge graphs as navigation aids, not source of truth.
- Keep command output compact when possible, but rerun the smallest failing command in raw mode when details are unclear.
- Do not hide failures, exit codes, stack traces, or actionable diagnostics.

## Safety and Code Rules

- Preserve user-owned changes and keep work scoped to the request.
- Follow existing patterns before introducing abstractions or dependencies.
- Do not change public APIs without updating relevant docs or specifications.
- Do not modify generated files manually.
- Do not expose secrets or weaken security checks without explicit authorization.
- Prefer recoverable operations and targeted tests before broad suites.

## Response Style

- Lead with the result, decision, or current blocker.
- Keep progress updates concise and concrete.
- State material assumptions and uncertainty explicitly.
- For code changes, report files changed, checks run, and remaining risks.

## Definition of Done

- Relevant tests pass.
- Lint and type checks pass when applicable.
- Agent assets pass `make validate-agent-assets` when they change.
- Documentation and verified memory are updated when durable behavior changes.
- The final response includes changed files, commands run, and risks.

## References

- Context routing: `docs/agent/INDEX.md`
- Commands and tools: `docs/agent/COMMANDS.md`, `docs/agent/TOOLS.md`
- Codex customization: `docs/agent/CODEX_CUSTOMIZATION.md`
- Skills and memory: `docs/agent/AGENTS_AND_SKILLS.md`, `docs/agent/MEMORY_POLICY.md`
