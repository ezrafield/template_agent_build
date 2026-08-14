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
| `code-review` | Perform a findings-first, read-only change review. |
| `architecture-decision` | Compare consequential options and record durable decisions. |
| `agent-setup` | Bootstrap or audit the installed agent kit. |
| `task-handoff` | Capture concise continuation state for multi-step work. |
| `memory-maintenance` | Promote, validate, or retire semantic and procedural memory. |
| `plan-evolution` | Record plans and upgrades, then compare strategy with outcome evidence and learning. |

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

- Put all activation conditions in the skill description because Codex sees it
  before loading the body.
- Keep one primary job per skill and keep `SKILL.md` below 4 KiB.
- Put optional details one reference hop from `SKILL.md` and load them only when
  the task needs them.
- Keep CLI dependencies in `agentkit-manifest.json`; `agents/openai.yaml`
  currently declares only supported MCP dependencies.

## v0.2 Skill Migration

| Removed name | v0.3 replacement |
| --- | --- |
| `code-search` | `repo-navigator` |
| `docs-sync` | Documentation step inside `safe-implementation` |
| `knowledge-graph-search` | Optional source-understanding reference in `repo-navigator` |
| `source-understanding` | Optional source-understanding reference in `repo-navigator` |
| `understand-refresh` | Installed Understand Anything plugin or `make understand` |

The v0.3 updater backs up and prunes only obsolete files previously recorded in
`.agentkit-installed-files`. It never prunes merged entrypoints,
copy-if-missing memory, or unrecorded project files.

## Claude Code Compatibility

Claude Code subagent templates remain under `.claude/agents/`, and optional
hook examples remain under `.claude/hooks/`. Codex skill discovery and runtime
guardrails are the v0.3 primary target; behavioral parity is not implied.

## Long-Term Memory

Keep raw episodic state in `.agent/tasks/`. Promote only reviewed, reusable,
non-sensitive facts or procedures into `.agent/memory/`, update the index, and
run `make audit-memory`. Current source, tests, and docs always override memory.
