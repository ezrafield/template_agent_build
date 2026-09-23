# Agent Kit Analysis

This template is now stronger as a reusable agent kit because it is not only a clean project layout. It can be installed into an existing project, refreshed later, and audited for context drift.

## Highest-Value Pieces

1. Progressive context loading
   - The shared `AGENTS.md` stays short.
   - `docs/agent/INDEX.md` routes agents to the smallest useful docs.
   - `docs/agent/CODEMAP.md` and module cards hold durable source context.

2. Installer and manifest
   - `agentkit-manifest.json` separates harness files, merge files, copy-if-missing files, project-local files, exclusions, and symlinks.
   - `install.sh` and `update.sh` install the kit into real projects.
   - `scripts/agentkit_installer.py` backs up existing agent config, merges managed blocks into `AGENTS.md`, preserves project-local files, writes `.agentkit-version`, and records `.agentkit-installed-files`.

3. Setup skill
   - `.agents/skills/agent-setup/SKILL.md` defines the workflow.
   - `scripts/agent_setup.py` detects stack and commands, refreshes `docs/agent/CODEMAP.md`, creates missing module cards, ensures task scaffolding exists, and runs validation.

4. Deterministic audit tools
   - `scripts/validate_agent_docs.py`
   - `scripts/check_context_staleness.py`
   - `scripts/audit_module_cards.py`
   - `scripts/audit_task_logs.py`
   - `scripts/detect_large_agent_files.py`

5. Lightweight plan lifecycle
   - `.agent/plans/active/`
   - `.agent/plans/completed/`
   - `.agent/plans/backlog/`
   - `.agent/plans/reports/`
   - `.agent/plans/template.md`

6. Minimal hooks
   - `.claude/hooks/block-secret-output.sh`
   - `.claude/hooks/warn-large-agent-files.sh`

## Reusable Skills

These should remain general and reusable across projects:

- `repo-navigator`: find relevant files without scanning the whole repository.
- `safe-implementation`: make the smallest safe change and verify it.
- `test-debug-loop`: reproduce, isolate, patch, and rerun targeted tests.
- `code-review`: review correctness, security, architecture drift, and tests.
- `docs-sync`: update durable docs when behavior changes.
- `architecture-decision`: decide and record architectural tradeoffs.
- `task-handoff`: preserve work state for continuation or audit.
- `source-understanding`: use graph-backed source discovery when available.
- `knowledge-graph-search`: query source graphs without loading huge files.
- `understand-refresh`: refresh source understanding artifacts.
- `agent-setup`: bootstrap project-specific agent context.

## Deterministic Scripts

Scripts are better than asking another agent when the work is repeatable, cheap, and auditable.

| Script | Why it matters |
| --- | --- |
| `generate_codemap.py` | Saves file-discovery tokens. |
| `update_module_cards.py` | Keeps module cards present as source folders change. |
| `agent_setup.py` | Creates a practical first pass of project context. |
| `agentkit_installer.py` | Makes the kit installable and updatable. |
| `run_targeted_tests.py` | Prevents expensive broad test loops too early. |
| `summarize_changed_files.py` | Makes handoff and review cheaper. |
| `validate_agent_docs.py` | Prevents missing agent docs and skills. |
| `check_context_staleness.py` | Warns when generated context may be stale. |
| `audit_module_cards.py` | Keeps module cards useful, not just present. |
| `audit_task_logs.py` | Keeps task notes auditable. |
| `detect_large_agent_files.py` | Protects auto-loaded context budgets. |
| `check_architecture_boundaries.py` | Catches simple layer violations. |
| `collect_task_trace.py` | Captures changed-file state for handoff. |

## Claude Subagents

Keep the default subagent set small:

- `repo-researcher`: read-only code discovery.
- `code-reviewer`: post-change review.
- `test-debugger`: failing tests and runtime errors.
- `security-reviewer`: auth, secrets, permissions, and sensitive data.
- `docs-maintainer`: synchronize module cards and durable docs.
- `understand-researcher`: graph-backed source research.

Add project-specific subagents only after repeated project-specific mistakes appear.

## Project-Specific Assets

Create project-specific skills or subagents when general guidance cannot know the rules.

Good examples:

- Domain rules for regulated or specialized data.
- Evaluation runners for AI pipelines.
- Migration reviewers for database-heavy systems.
- Release gatekeepers for deployment readiness.
- API contract change workflows for backend-heavy projects.
- Retrieval or evidence-checking skills for RAG projects.

Avoid adding project-specific assets too early. The default kit should stay small enough that agents actually follow it.

## Current Verdict

The template is stronger after the installer, setup skill, audit scripts, plan lifecycle, and minimal hooks.

The tradeoff is more maintenance surface. The highest-risk piece is now `scripts/agentkit_installer.py`, because it writes into existing projects. It should stay well tested with temp-directory tests that verify merge, backup, copy-if-missing, update, and installed-file behavior without creating permanent test fixtures.

## Next Improvements

1. Add a formal test suite for `scripts/agentkit_installer.py` when the project is ready to keep tests.
2. Add a dry-run mode to the installer.
3. Add a small Windows wrapper, such as `install.ps1`, if Windows users are a primary audience.
4. Make `check_context_staleness.py` hash-based if mtime warnings become noisy.
5. Keep hooks opt-in and warning-first.
