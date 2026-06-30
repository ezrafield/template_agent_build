# Agent-Native Project Template

This repository is a practical template for projects that collaborate well with
coding agents such as Codex, Claude Code, and similar tools.

The core idea is progressive context loading: keep auto-loaded instructions
short, route agents through a small index, and load richer docs only when the
task needs them. The template now also includes lightweight long-term memory so
future agents can reuse vetted lessons without reading old task logs.

The memory layer is inspired by PlugMem's semantic, procedural, and episodic
taxonomy, but stays dependency-free: Markdown cards, a JSON index, and small
deterministic Python scripts. It does not require embeddings, a graph database,
an API key, or a model server.

## How Agents Use It

For non-trivial work, agents should:

1. Read `AGENTS.md` or `CLAUDE.md`.
2. Route through `docs/agent/INDEX.md`.
3. Check `.agent/memory/index.json` for relevant semantic or procedural memory.
4. Verify memory against current code, tests, and docs.
5. Read the relevant module card or `docs/agent/CODEMAP.md`.
6. Use Semble, `rg`, Serena, or Understand Anything only as the task requires.
7. Make the smallest safe change and run targeted checks before broad checks.
8. Capture task state and reusable lessons when useful.

Memory is a decision aid, not source of truth. Current repository files win when
they conflict with memory.

## Structure

- `AGENTS.md` and `CLAUDE.md`: short agent entrypoints.
- `docs/agent/`: on-demand routing docs, module cards, policies, and tool notes.
- `.agent/memory/`: semantic and procedural long-term memory.
- `.agent/tasks/`: episodic task logs and audit trails.
- `.agent/plans/`: lightweight plan lifecycle folders and template.
- `.agents/skills/`: reusable Codex-style skill templates.
- `.claude/agents/`: Claude Code subagent templates.
- `.claude/hooks/`: optional lightweight hook examples.
- `.mcp/`: MCP setup notes and candidate server documentation.
- `tools/agent/`: pinned manifests for project-local optional agent tools.
- `.understand-anything/`: Understand Anything setup notes.
- `scripts/`: deterministic helpers for setup, audits, context generation, and memory.
- `eval/`: retrieval and regression evaluation placeholders.
- `src/` and `tests/`: sample project modules and tests.

## Tool Roles

| Tool | Solves | Best place in template |
| --- | --- | --- |
| Module cards | Human-maintained ownership, interfaces, tests, and pitfalls | Stable context anchor |
| Memory | Durable lessons from previous tasks | Decision aid before search |
| Semble | Natural-language code and docs retrieval | Context discovery |
| `rg` | Exact string, symbol, and path confirmation | Verification |
| Serena | References, declarations, diagnostics, and safe refactors | Advanced coding setup |
| ast-grep | Structural code search | Pattern matching |
| Repomix | Repository export/bundling | External model review |
| RTK | Compressed noisy terminal output | Command execution |
| Understand Anything | Graph and dependency reasoning | Architecture understanding |

## Getting Started

```bash
make install
make agent-tools-check
make test-unit
make lint
```

This is a template, so most project commands are placeholders until you wire
them to your actual stack.

## Project-Local Agent Tools

Optional agent tools are pinned under `tools/agent/` so a fresh checkout can
recreate the same local tool stack without global installs:

```bash
make agent-tools-install
make agent-tools-check
```

If `make` is not available on Windows, use:

```bash
python scripts/bootstrap_agent_tools.py
python scripts/bootstrap_agent_tools.py --check
```

Prerequisites are deliberately small and machine-level: Python, `uv`, Node.js
22+, and `npm`. The bootstrap handles the project-local pieces after that.

What is committed:

- Semble manifest and lock: `tools/agent/python/semble/`
- Serena manifest and lock: `tools/agent/python/serena/`
- Repomix and ast-grep npm manifest and lock: `tools/agent/package*.json`
- RTK release manifest and checksums: `tools/agent/rtk-manifest.json`
- Bootstrap and wrapper scripts under `scripts/`

What is generated and ignored:

- Python virtual environments under `tools/agent/python/*/.venv/`
- Node dependencies under `tools/agent/node_modules/`
- RTK binary under `tools/agent/bin/`
- uv, npm, Hugging Face, Semble, and download caches

Semble and Serena intentionally use separate `uv` environments. Serena
`1.5.3` pins `pathspec==0.12.1`, while Semble search needs a newer `pathspec`
API, so splitting the environments preserves both pinned tools and keeps
`semble search` working. Python 3.13 is requested for these environments to
avoid Python 3.14 compatibility warnings in Serena's dependencies.

Run tools through the workspace wrapper when you do not want to rely on PATH:

```bash
make code-search QUERY="source understanding" CONTENT=all
make git-status
python scripts/run_agent_tool.py semble search "source understanding" . --content all
python scripts/run_agent_tool.py serena --help
python scripts/run_agent_tool.py repomix --version
python scripts/run_agent_tool.py ast-grep --version
```

On a copied workspace, rerun `make agent-tools-install` or
`python scripts/bootstrap_agent_tools.py` if the OS, CPU architecture, Python,
Node, or absolute path changed.

## Installing Into Another Project

From a checkout of this template:

```bash
./install.sh /path/to/project
```

The installer reads `agentkit-manifest.json`, backs up existing agent config
under `.agentkit/backups/`, merges `AGENTS.md` and `CLAUDE.md`, copies harness
files, copies starter `.agent/` files only when missing, and records installed
paths in `.agentkit-installed-files`.

Use `./update.sh /path/to/project` to refresh the harness later.

After install, run:

```bash
python scripts/agent_setup.py
make agent-tools-install
```

If `make` is unavailable, run `python scripts/bootstrap_agent_tools.py`
instead.

The setup script detects the stack and common commands, refreshes
`docs/agent/CODEMAP.md`, creates missing module cards, ensures task and memory
scaffolding exists, and runs validation.

## Agent Memory Workflow

Use `.agent/tasks/` for raw episodic notes. Promote only compact, reusable,
non-sensitive lessons into `.agent/memory/`.

| Memory type | Purpose | Location |
| --- | --- | --- |
| Semantic | Stable facts, conventions, and decisions | `.agent/memory/semantic/` |
| Procedural | Reusable workflows and playbooks | `.agent/memory/procedural/` |
| Episodic | Raw task context and audit history | `.agent/tasks/` |

```bash
make extract-task-memory TASK=.agent/tasks/<task>.md
make audit-memory
```

The extraction script creates a candidate under `.agent/memory/candidates/`.
Review it manually, remove unsafe or low-value details, move durable facts into
`semantic/` or workflows into `procedural/`, update `.agent/memory/index.json`,
then run the audit again.

`make audit-memory` validates index metadata, card structure, source-task and
related-file links, verification dates, and a 180-day staleness threshold.
Candidates are drafts and are excluded from installation; only reviewed,
indexed memory is intended for reuse.

Never promote secrets, credentials, customer data, sensitive stack traces, or
unverified one-off conclusions. Memory narrows the search; current code, tests,
specifications, and agent docs remain authoritative.

## Audits And Verification

```bash
make validate-agent-docs
make check-context-staleness
make audit-module-cards
make audit-task-logs
make audit-memory
make detect-large-agent-files
make detect-large-context-docs
```

Use audits as warnings during setup and stricter gates before sharing the kit
with a team.

## Source Understanding

Use Understand Anything to generate a knowledge graph for humans and agents:

```bash
make understand
make understand-search QUERY="api route"
```

Generated graph files are ignored by default; setup notes and ignore rules are
committed.

## Credits

See [`CREDITS.md`](CREDITS.md) for the open-source projects that influenced this
template and the optional tools it is designed to work with.
