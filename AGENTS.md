# AGENTS.md

## Project Purpose

This agent-native template demonstrates progressive context, skills, deterministic validation, and project memory.

## Instruction Hierarchy

- Read this file before non-trivial work, then route through `docs/agent/INDEX.md`.
- Codex loads at most one instruction file per directory from the repository root to the working directory. At one level, `AGENTS.override.md` is preferred over `AGENTS.md`; ancestors remain active.
- Use a root override only temporarily; use nested instructions for durable directory guidance.
- Project instructions and skills do not override system, managed, safety, or explicit user constraints.

## Plan Evolution Rule

- Before executing any explicit plan, roadmap, strategy change, migration, or version upgrade—or whenever work is organized as a multi-step plan—use `$plan-evolution` and create or update its Markdown record under `.agent/plans/`.
- Keep the record current with goals, strategy, signals, decisions, evidence, and user/AI learning; move closed records to `completed/`.
- Create one linked record per material upgrade. Read-only answers and unplanned one-step actions are exempt. Never store secrets, private data, or hidden chain-of-thought.

## Default Workflow

1. Understand the task and keep its scope explicit.
2. Read `docs/agent/INDEX.md`, then build and inspect a task-context bundle for non-trivial work with `python scripts/task_context.py build "<task>"`.
3. Review warnings, gaps, hashes, selections, and drops; routes are authoritative and Semble is advisory.
4. Check `.agent/memory/index.json` for relevant guidance, then verify memory and generated excerpts against current files.
5. Before full-file reads, use `rg` for exact checks and symbol tools for references or refactors.
6. Before editing, identify the selected files, why they matter, and the main uncertainty or risk.
7. Make the smallest safe change and update tests or docs when behavior changes.
8. Run targeted checks before broader checks.
9. Report changed files, commands run, and remaining risks.

## Context Rules

- Do not scan the whole repository unless the task requires it.
- Prefer the task-context bundle, module cards, targeted reads, and deterministic scripts over broad context loading.
- Treat generated bundles as disposable ignored cache data; never promote them automatically into task logs or memory.
- Treat memory and generated knowledge graphs as navigation aids, not source of truth.
- Keep output compact; rerun the smallest failing command raw when unclear.
- Do not hide failures, exit codes, stack traces, or actionable diagnostics.

## Safety and Code Rules

- Preserve user-owned changes and keep work scoped to the request.
- Follow existing patterns before adding abstractions or dependencies.
- Do not change public APIs without updating relevant docs or specifications.
- Do not modify generated files manually.
- Do not expose secrets or weaken security checks without explicit authorization.
- Prefer recoverable operations and targeted tests.

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
