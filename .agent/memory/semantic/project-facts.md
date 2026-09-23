# Memory: Project Facts

Type: semantic
Scope: project
Confidence: high
Last verified: 2026-09-23
Source task: .agent/tasks/README.md
Verification record: .agent/memory/verification/2026-09-23-token-efficiency.md

## When to use

Use this memory when orienting on the template's purpose and baseline workflow.

## Content

- This template prioritizes effective task completion with low context, execution, and maintenance cost; research evaluations are optional.
- Agents start with the shared `AGENTS.md`, then reuse an inspected current bundle or compile task-specific Markdown for non-trivial work. Claude native-support requirements are documented in CODEX_CUSTOMIZATION.md.
- `.agent/tasks/` is episodic memory: task-local notes and audit trails.
- `change_logs/YYYY-MM-DD.md` holds concise daily AI change summaries; logs belong to the project and are preserved across kit updates.
- `.agent/memory/` is long-term semantic and procedural memory that must be verified before use.
- The Codex-first v0.5 catalog contains eleven discoverable skills under `.agents/skills/`, including `test-scope` for minimal necessary coverage.
- `docs/agent/context-routes.json` is the validated route source; `INDEX.md` is its synchronized human explanation.
- Task bundles are reproducible ignored cache files under `.agent/context-cache/task-context/`, not authoritative memory.
- Active Codex hooks and command rules are machine-local opt-in files generated from `.codex/templates/`.
- Memory index version 1 accepts existing entries without evidence as untracked; new or re-verified entries record reviewed source fingerprints.
- `scripts/memory_lookup.py` provides compact summaries, paths, and current evidence status; full fingerprints remain available to validators.
- Reliability evaluations measure explicit task outcomes; live effectiveness remains unmeasured until matched live trials run.

## Related files

- `AGENTS.md`
- `docs/agent/INDEX.md`
- `docs/agent/context-routes.json`
- `scripts/task_context.py`
- `scripts/memory_lookup.py`
- `docs/agent/MEMORY_RETRIEVAL.md`
- `.agent/tasks/README.md`
- `agentkit-manifest.json`
- `docs/agent/CODEX_CUSTOMIZATION.md`
- `docs/agent/MEMORY_POLICY.md`
- `docs/agent/RELIABILITY_EVALS.md`

## Staleness triggers

- Root agent entrypoints change.
- The context routing workflow changes.
- Task-context route schema, safety policy, or bundle format changes.
- The task-log or memory folder layout changes.
- The manifest skill catalog or guardrail activation model changes.
