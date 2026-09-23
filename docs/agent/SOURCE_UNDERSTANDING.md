# Source Understanding

Use CODEMAP/module cards, Semble, `rg`, optional Serena, and Understand Anything as layered source-understanding tools for humans and agents.

## Purpose

Start with the low-cost default stack:
- A current compact task-context bundle
- `docs/agent/CODEMAP.md`
- Module cards
- `rg` exact confirmation

Use optional Semble search when the routed context leaves a concrete discovery gap.

Use Serena for symbol references, declarations, diagnostics, and safe refactors when language-server semantics matter.

Understand Anything generates a code knowledge graph at:

```txt
.understand-anything/knowledge-graph.json
```

That graph can support:
- Architecture discovery
- Component and dependency search
- Guided onboarding tours
- Code question answering
- Diff and risk analysis
- Human review and agent handoff

## Human Workflow

1. When graph-based exploration helps, reuse a current graph or generate/refresh one if it is missing or stale.
2. Open the dashboard when visual exploration helps.
3. Ask graph-backed questions before scanning the whole repository.
4. Use source links from the graph to inspect actual files.

Commands for optional search and graph exploration:

```bash
make code-search QUERY="auth service" CONTENT=all
make understand
make understand-dashboard
make understand-search QUERY="auth service"
```

`make understand` and `make understand-dashboard` print runtime guidance; they do
not generate a graph or launch a dashboard. Those actions use the separately
installed Understand Anything runtime, such as `/understand` and
`/understand-dashboard`.

If `make` is unavailable, use `python scripts/run_agent_tool.py semble search "auth service" . --content all` for Semble and the Python graph helper scripts directly.

## Agent Workflow

Before broad source exploration:

1. Follow `docs/agent/INDEX.md`: reuse a current inspected task-context bundle, or build one when the task, route, requested ranges, or relevant sources change.
2. Read compact output first, including the relevant CODEMAP/module-card excerpts. Use `python scripts/memory_lookup.py "<task>"` for relevant memory; do not reload unchanged material for a new skill.
3. Fill remaining gaps with `rg`, optional Semble search, and `docs/agent/CODE_SEARCH.md` as needed.
4. When architecture or dependency relationships require graph exploration, check `.understand-anything/knowledge-graph.json` and use it if current. If that needed graph is missing or stale, use the installed runtime to generate/refresh it; `make understand` shows the runtime instructions.
5. Verify conclusions against targeted current source reads. Open the full context audit when selection or provenance needs inspection.

## What To Commit

Commit:
- `.understand-anything/README.md`
- `.understand-anything/.understandignore`
- `.understand-anything/config.example.json`
- Docs and scripts that explain how to use the graph

Usually ignore:
- `.understand-anything/knowledge-graph.json`
- `.understand-anything/meta.json`
- `.understand-anything/intermediate/`
- `.understand-anything/tmp/`
- Generated graph variants unless the team explicitly wants them versioned

## Search Strategy

When a question requires graph-based dependency exploration:

1. Search node names, summaries, and tags in the graph.
2. Follow connected edges for imports, calls, tests, and documents.
3. Identify the architectural layer.
4. Read only the few relevant source files.
5. Summarize the answer with file paths and relationships.

## Refresh Policy

Refresh only when the task will use the graph and relevant source changes have
made it stale. Adding or moving modules and large refactors are reasons to check
freshness before graph-based onboarding, architecture review, or broad exploration.

If targeted context and source reads answer the question, no graph generation or
refresh is needed. A graph remains a navigation aid, not source authority.
