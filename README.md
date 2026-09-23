# Agent-Native Project Template

A lightweight kit for completing coding tasks effectively with less context,
execution, and maintenance overhead. Use a small instruction entrypoint,
task-specific context, reusable skills, and reviewed memory with Codex or another
coding assistant. Keep the workflow proportional to the task.

**Agent-kit version: 0.5.0.** The sample application has its own version, 0.1.0.
The core uses Python's standard library and Markdown/JSON files. It needs no API
key, vector database, model server, or always-running orchestrator.

## Start With the Core

From a checkout, use Python 3.11 or newer, Git, and `rg` on PATH:

```bash
python scripts/validate_agent_assets.py
python scripts/task_context.py build "Fix a login validation bug" --no-search
python scripts/memory_lookup.py "debugging"
```

Read the emitted `.read.md` bundle. These commands validate the kit, build local
context, and look up memory. No model calls or optional
tool installation are involved. Use the Python interpreter configured for your
environment if `python` is unavailable.

To run the template's tests, install `pytest>=8,<9` in your development environment
and run `python -m pytest -q`. With `uv`, an isolated alternative is:

```bash
uv run --no-project --with "pytest>=8,<9" python -m pytest -q
```

`make` shows help and provides optional shortcuts. `make install` installs the **optional
agent tool stack**, so use the commands above for the minimal path. The sample
`dev` and `typecheck` targets are placeholders; `lint` compiles Python and validates
agent assets. Connect real application commands when adopting the template.

## Install Into an Existing Project

Run these commands from the template checkout, substituting your destination:

```bash
python scripts/agentkit_installer.py install --source . --target "/path/to/project"
python scripts/agentkit_installer.py check --source . --target "/path/to/project"
```

Then run `python scripts/agent_setup.py` **from the destination project**. Review
its detected commands, generated codemap, and module-card TODOs. The setup adapts
agent documentation; it does not install your application's dependencies.

To update later, run from the template checkout:

```bash
python scripts/agentkit_installer.py update --source . --target "/path/to/project"
```

The installer backs up replaced kit files, merges root instructions, and copies
starter memory only when missing. It prunes only obsolete recorded kit-owned
paths. Application files, project Makefiles, and existing project memory retain
their ownership. Shell wrappers `install.sh` and `update.sh` are also available.

## Everyday Workflow

1. Start with `AGENTS.md`, then use the [context index](docs/agent/INDEX.md).
2. Reuse an inspected current bundle for the same task and route. Rebuild when
   the task, options, requested ranges, or relevant sources change.
3. Read compact warnings, gaps, source identities, and excerpts. Query memory with
   `python scripts/memory_lookup.py "your task"`, then verify useful cards against source.
4. State observable acceptance criteria, make the smallest complete change, and
   run focused checks. Use `test-scope` when adding or pruning coverage; reuse
   relevant tests and update only necessary docs. Multi-module behavior or public-contract changes require
   independent review under the existing implementation/review skills.
5. Keep required plans under `.agent/plans/`; link their goals and check results
   from concise handoff checkpoints instead of duplicating the same narrative.
6. After each AI change task, append a brief summary, key paths, and check results
   to `change_logs/YYYY-MM-DD.md` (local date). Reuse the daily file and preserve
   earlier entries. Logs stay project-owned across kit updates; read-only tasks
   need no entry.

The router uses deterministic rules. Semble search is optional and advisory;
Jev advice never controls routes, permissions, context expansion, or completion.
Current source remains authoritative over memory and generated artifacts.

Context has a 10-document and 40,000-character reading limit. Full audits,
explicit expansion, and route overrides are described in the
[context guide](docs/agent/CONTEXT_ROUTER.md). Memory promotion stays manual;
new or re-verified cards need reviewed source evidence. Follow the
[promotion rules](docs/agent/MEMORY_PROMOTION_RULES.md).

## Small Core, Optional Experiments

The reference template enforces **fewer than 50 collected pytest cases**,
including parameterized cases and skips. Keep one useful check for each important
contract; replace redundant coverage before adding more. The reusable
[`test-scope` skill](.agents/skills/test-scope/SKILL.md) follows each project's
budget, rather than imposing this template's cap on every project.

Routine CI runs the core suite, compilation, and agent-asset validation. Detailed
research corpora remain in `eval/` for explicit experiments; they do not run as
part of pytest or routine CI. Use the manual `agent-doc-check` workflow or the
[evaluation guide](docs/agent/RELIABILITY_EVALS.md) when investigating the kit itself.

Assess performance using completed acceptance criteria, elapsed time, context,
and commands. Smaller test or document counts alone do not establish better task
outcomes. Live effectiveness remains **not yet measured**.

## Optional Integrations

Claude Code uses the same `AGENTS.md`; see [native support and migration](docs/agent/CODEX_CUSTOMIZATION.md#claude-code) for version/session requirements.

Install optional tools only when their capabilities are useful. The [tool workspace guide](tools/agent/README.md)
covers pinned Semble, Serena, Repomix, ast-grep, and RTK installations, their
additional prerequisites, isolated environments, and ignored caches.

- Use `rg` for exact search and Semble for advisory natural-language retrieval.
- Use Serena for language-server navigation; export repositories with Repomix when needed.
- Use RTK to reduce noisy terminal output while preserving actionable errors.
- Use Understand Anything through its installed runtime for knowledge graphs.
  `make understand` prints setup guidance; it does not generate a graph itself.

Hooks and command rules are **opt-in**. Fresh installs do not activate them.
See [Codex customization](docs/agent/CODEX_CUSTOMIZATION.md) for generation, trust,
and validation. Check [component versions](docs/agent/COMPONENT_VERSIONS.md) before
planning dependency upgrades; a newer release alone does not establish compatibility.

## Documentation Map

| Need | Start here |
| --- | --- |
| Agent entrypoints and task routing | [AGENTS.md](AGENTS.md), [context index](docs/agent/INDEX.md) |
| Context selection, budgets, expansion | [Context router](docs/agent/CONTEXT_ROUTER.md) |
| Commands and tools | [Generated commands](docs/agent/COMMANDS.md), [tool reference](docs/agent/TOOLS.md) |
| Skills, review, and handoff | [Skills](docs/agent/AGENTS_AND_SKILLS.md), [workflows](docs/agent/WORKFLOWS.md) |
| Memory and promotion | [Memory policy](docs/agent/MEMORY_POLICY.md), [promotion rules](docs/agent/MEMORY_PROMOTION_RULES.md) |
| Code and architecture discovery | [Source understanding](docs/agent/SOURCE_UNDERSTANDING.md) |
| Version and quality findings | [Versions](docs/agent/COMPONENT_VERSIONS.md), [completed work](.agent/plans/completed/) |

`src/` and `tests/` contain the sample application and test suites. `.agents/skills/`,
`scripts/`, `eval/`, and `docs/agent/` contain the reusable kit. `.agent/plans/` and
`.agent/tasks/` retain decisions and checkpoints; generated context, tool caches,
and evaluation reports are ignored. See [credits](CREDITS.md) for upstream tools
and design influences.
