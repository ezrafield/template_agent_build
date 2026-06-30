# Source Understanding

Use CODEMAP/module cards, Semble, `rg`, optional Serena, and Understand Anything as layered source-understanding tools for humans and agents.

## Purpose

Start with the low-cost default stack:
- `docs/agent/CODEMAP.md`
- Module cards
- Semble natural-language search
- `rg` exact confirmation

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

1. Generate or refresh the graph.
2. Open the dashboard when visual exploration helps.
3. Ask graph-backed questions before scanning the whole repository.
4. Use source links from the graph to inspect actual files.

Recommended commands:

```bash
make code-search QUERY="auth service" CONTENT=all
make understand
make understand-dashboard
make understand-search QUERY="auth service"
```

If `make` is unavailable, use `python scripts/run_agent_tool.py semble search "auth service" . --content all` for Semble and the Python graph helper scripts directly.

## Agent Workflow

Before broad source exploration:

1. Read `docs/agent/INDEX.md`.
2. Read `docs/agent/CODE_SEARCH.md` and this file.
3. Read `docs/agent/CODEMAP.md` or the relevant module card.
4. Use Semble and `rg` to identify likely files.
5. Check whether `.understand-anything/knowledge-graph.json` exists when architecture or dependency impact matters.
6. If it exists, search the graph before reading many files.
7. If it does not exist or is stale, recommend `make understand`.
8. Use targeted file reads for final verification.

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

For a question like "where is request validation handled?":

1. Search node names, summaries, and tags in the graph.
2. Follow connected edges for imports, calls, tests, and documents.
3. Identify the architectural layer.
4. Read only the few relevant source files.
5. Summarize the answer with file paths and relationships.

## Refresh Policy

Refresh the graph:
- After adding or moving modules.
- After large refactors.
- Before onboarding a new human or agent.
- Before architecture review.
- Before asking broad codebase questions.

For small isolated edits, graph refresh can wait until the end of the task.
