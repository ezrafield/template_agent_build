# AGENTS.md

## Project Purpose

Help agents complete tasks effectively with low context, execution, and maintenance cost. Keep tests and docs proportional; research harnesses are optional.

## Instruction Hierarchy

- Read this file before non-trivial work, then route through `docs/agent/INDEX.md`.
- Codex loads one instruction file per directory, root to working directory. `AGENTS.override.md` replaces same-level `AGENTS.md`; ancestors remain active.
- Use a root override only temporarily; use nested instructions for durable directory guidance.
- Project instructions and skills do not override system, managed, safety, or explicit user constraints.

## Plan Evolution Rule

- Before any plan, roadmap, strategy change, migration, version upgrade, or multi-step execution, use `$plan-evolution` and create/update its record under `.agent/plans/`.
- Keep the record current with goals, strategy, signals, decisions, evidence, and user/AI learning; move closed records to `completed/`.
- Create one linked record per material upgrade. Read-only answers and unplanned one-step actions are exempt. Never store secrets, private data, or hidden chain-of-thought.

## Default Workflow

1. Understand the task and keep its scope explicit.
2. For non-trivial work, reuse current inspected context or run `python scripts/task_context.py build "<task>"` after routing through the index.
3. Inspect compact warnings, gaps, and sources; open the full audit when needed. Routes are authoritative; Semble is advisory.
4. Query memory with `python scripts/memory_lookup.py "<task>"`; verify relevant cards against current source.
5. Use `rg` and symbol tools before full-file reads.
6. Before editing, identify relevant files, their purpose, and the main risk.
7. Make the smallest complete change. Use `test-scope` when adding/pruning tests; reuse coverage and update only necessary docs.
8. Run targeted checks before broader checks.
9. After AI edits, before responding or handing off, append a concise summary to `change_logs/YYYY-MM-DD.md` using the local date. Create it as needed; reuse that day's file and preserve earlier entries. Include changes, key paths, and checks/pending work; omit secrets and private data. Read-only tasks need no entry.
10. Report changed files, commands run, and remaining risks.

## Context Rules

- Do not scan the whole repository unless the task requires it.
- Reuse read context for the same task and route; rebuild when relevant sources or requested ranges change.
- Prefer compact bundles, module cards, targeted reads, and deterministic scripts.
- Bundles are disposable ignored cache data; never promote them automatically into logs or memory.
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

## Definition of Done

- Relevant tests and applicable lint/type checks pass.
- Agent assets pass `make validate-agent-assets` when they change.
- Documentation and verified memory are updated when durable behavior changes.

## References

- Context routing: `docs/agent/INDEX.md`
- Commands and tools: `docs/agent/COMMANDS.md`, `docs/agent/TOOLS.md`
- Codex customization: `docs/agent/CODEX_CUSTOMIZATION.md`
- Skills and memory: `docs/agent/AGENTS_AND_SKILLS.md`, `docs/agent/MEMORY_POLICY.md`
