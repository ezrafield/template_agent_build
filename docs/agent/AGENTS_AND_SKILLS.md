# Agents and Skills

This repository ships a small Codex-first skill catalog plus Claude Code
subagent templates. Repository skills live in `.agents/skills/` and use the
open agent skills format: required `name` and `description` frontmatter, a
concise workflow body, and Codex UI metadata under `agents/openai.yaml`.

## Core Skills

| Skill | Use |
| --- | --- |
| `repo-navigator` | Locate relevant code, tests, docs, symbols, and optional graph context without editing. |
| `safe-implementation` | Implement scoped behavior changes with tests and synchronized documentation. |
| `test-debug-loop` | Reproduce, isolate, fix, and re-test a failure. |
| `test-scope` | Minimize necessary coverage, remove redundant cases, and respect the project's test budget. |
| `code-review` | Perform a findings-first, read-only change review. |
| `architecture-decision` | Compare consequential options and record durable decisions. |
| `agent-setup` | Bootstrap or audit the installed agent kit. |
| `task-handoff` | Capture concise continuation state for multi-step work. |
| `memory-maintenance` | Promote, validate, or retire semantic and procedural memory. |
| `plan-evolution` | Record plans and upgrades, then compare strategy with outcome evidence and learning. |
| `task-context` | Build, explain, or evaluate deterministic Markdown context bundles. |

The manifest is the source of truth for required and optional command
dependencies. Skill versions inherit the agent-kit version; do not add a
parallel skill lockfile for repository-owned skills.

## Plan Evolution Records

`.agent/plans/` is the durable source for plans and upgrades. Start from
`template.md`, keep work in `active/` or `backlog/`, move closed records to
`completed/`, and reserve `reports/` for comparisons across records. Each
material version upgrade gets its own linked file. Records capture explicit
strategy hypotheses, observable evidence, and learning for both the user and AI
workflow without storing secrets or hidden chain-of-thought.

## Progressive Disclosure

For changes spanning multiple modules' behavior or public contracts, use the
existing implementation and review skills with observable acceptance criteria
and an independent reviewer. See [RELIABILITY_EVALS.md](RELIABILITY_EVALS.md).
No always-running reviewer is installed. `test-scope` applies when designing or
pruning coverage; an ordinary test run does not need another skill activation.

Skill activation reuses already-inspected context for the same task and route.
Refresh when relevant sources or requested ranges change. Read compact bundles
and memory lookup results first; keep full audit details available on demand.
Give independent reviewers focused criteria, diffs, and check evidence. Link
plan/checkpoint content rather than copying it into multiple logs.

- Put all activation conditions in the skill description because Codex sees it
  before loading the body.
- Keep one primary job per skill and keep `SKILL.md` below 4 KiB.
- Put optional details one reference hop from `SKILL.md` and load them only when
  the task needs them.
- Keep CLI dependencies in `agentkit-manifest.json`; `agents/openai.yaml`
  currently declares only supported MCP dependencies.

## Skill Migration

| Removed name | v0.3 replacement |
| --- | --- |
| `code-search` | `repo-navigator` |
| `docs-sync` | Documentation step inside `safe-implementation` |
| `knowledge-graph-search` | Optional source-understanding reference in `repo-navigator` |
| `source-understanding` | Optional source-understanding reference in `repo-navigator` |
| `understand-refresh` | Installed Understand Anything plugin or `make understand` |

The updater backs up and prunes only obsolete files previously recorded in
`.agentkit-installed-files`. It preserves current merged entrypoints,
copy-if-missing memory, and unrecorded project files. A retired `CLAUDE.md` gets
only its old kit block removed, with a backup; custom text is retained. See
[migration details](CODEX_CUSTOMIZATION.md#claude-code).

## Claude Code Compatibility

Claude Code subagent templates remain under `.claude/agents/`, and optional
hook examples remain under `.claude/hooks/`. Codex skill discovery,
task-context bundles, and runtime guardrails are the v0.5 primary target;
behavioral parity is not implied.

## Long-Term Memory

Keep raw episodic state in `.agent/tasks/`. Promote only reviewed, reusable,
non-sensitive facts or procedures into `.agent/memory/`, update the index, and
run `make audit-memory`. Current source, tests, and docs always override memory.
