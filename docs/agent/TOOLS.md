# Tools

Use deterministic scripts for repeatable, cheap, auditable work.

## Included Scripts

| Script | Purpose |
| --- | --- |
| `scripts/generate_codemap.py` | Refresh `docs/agent/CODEMAP.md` from source folders. |
| `scripts/agent_setup.py` | Detect stack and commands, refresh agent context, and run validation. |
| `scripts/agentkit_installer.py` | Install or update agent-kit files from `agentkit-manifest.json`. |
| `scripts/summarize_changed_files.py` | Summarize changed files for handoff and review. |
| `scripts/update_module_cards.py` | Create missing module cards from source folders. |
| `scripts/run_targeted_tests.py` | Run a focused test command or pick a small default. |
| `scripts/validate_agent_docs.py` | Validate required agent docs and skill templates. |
| `scripts/detect_large_context_docs.py` | Warn when auto-loaded docs become too large. |
| `scripts/detect_large_agent_files.py` | Warn when agent entrypoints, skills, or subagents become too large. |
| `scripts/check_context_staleness.py` | Warn when generated agent context may be older than source files. |
| `scripts/audit_module_cards.py` | Check module-card coverage, headings, and unresolved TODOs. |
| `scripts/audit_task_logs.py` | Check task logs for required audit headings. |
| `scripts/extract_task_memory.py` | Create a manually reviewed memory candidate from a task log. |
| `scripts/validate_memory_links.py` | Validate promoted memory cards, metadata, index entries, and linked files. |
| `scripts/audit_memory_staleness.py` | Warn when promoted memory is old or references missing files. |
| `scripts/check_architecture_boundaries.py` | Catch simple layer import violations. |
| `scripts/collect_task_trace.py` | Create a task trace from current changed files. |
| `scripts/search_understand_graph.py` | Search the Understand Anything graph without loading it all into context. |
| `scripts/validate_understand_graph.py` | Validate the expected graph shape before graph-backed work. |
| `scripts/bootstrap_agent_tools.py` | Recreate project-local Semble, Serena, Repomix, ast-grep, and RTK tools. |
| `scripts/run_agent_tool.py` | Run project-local tools without requiring global PATH setup. |
| `eval/retrieval/run_retrieval_eval.py` | Check whether Semble searches return expected context paths. |

## Command Output

RTK is an optional output-compression layer for noisy local commands. Use the compact make targets when available; they prefer the workspace-local RTK binary and fall back to the raw command only when RTK is missing.

## Project-Local Tools

Pinned tool manifests live in `tools/agent/`. Commit manifests and lockfiles, but do not commit generated environments, caches, or binaries.

```bash
make agent-tools-install
make agent-tools-check
python scripts/run_agent_tool.py semble --help
python scripts/run_agent_tool.py rtk --version
```

If `make` is unavailable, run `python scripts/bootstrap_agent_tools.py` and `python scripts/bootstrap_agent_tools.py --check` directly.

Prerequisites:
- Python
- `uv`
- Node.js 22+
- `npm`

Committed manifests:
- `tools/agent/python/semble/pyproject.toml` and `uv.lock`
- `tools/agent/python/serena/pyproject.toml` and `uv.lock`
- `tools/agent/package.json` and `package-lock.json`
- `tools/agent/rtk-manifest.json`

Generated and ignored:
- `tools/agent/python/*/.venv/`
- `tools/agent/node_modules/`
- `tools/agent/bin/`
- `tools/agent/.uv-cache/`
- `tools/agent/.npm-cache/`
- `tools/agent/.hf-cache/`
- `.agent/context-cache/semble/`

Semble and Serena use separate `uv` environments because Serena pins `pathspec==0.12.1`, while Semble search needs a newer `pathspec` API.

## Make Targets

```bash
make docs-map
make agent-setup
make agent-tools-install
make agent-tools-check
make update-module-cards
make targeted-tests
make validate-agent-docs
make detect-large-context-docs
make detect-large-agent-files
make check-context-staleness
make audit-module-cards
make audit-task-logs
make extract-task-memory TASK=.agent/tasks/<task>.md
make validate-memory-links
make audit-memory-staleness
make audit-memory
make check-architecture-boundaries
make task-trace
make code-search QUERY="service" CONTENT=all
make repomix
make ast-grep PATTERN="def $NAME($$$ARGS): $$$BODY" LANG=python
make rtk-gain
make git-status
make git-diff
make test-unit-compact
make lint-compact
make typecheck-compact
make understand
make understand-search QUERY="service"
make validate-understand-graph
make retrieval-eval
```

## Tool Principles

- Prefer scripts for deterministic checks.
- Prefer Semble + `rg` + CODEMAP/module cards for normal retrieval.
- Keep Serena optional for language-server backed symbol work.
- Use Repomix as an export tool, not as the normal daily retrieval workflow.
- Prefer targeted checks before broad suites.
- Use memory as guidance only; verify it before editing.
- Keep scripts safe by default.
- Make script output easy for humans and agents to inspect.
- Compress noisy terminal output when possible, but keep raw reruns available for unclear failures.
- Avoid hiding policy decisions inside scripts; document decisions in ADRs.
