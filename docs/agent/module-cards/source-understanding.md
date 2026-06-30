# Module: Source Understanding

## Responsibility
Provides knowledge-graph based source discovery, search, onboarding, and architecture exploration.

## Key Files
- `docs/agent/CODE_SEARCH.md`: Semble, `rg`, Serena, and Repomix retrieval guidance
- `docs/agent/CONTEXT_ROUTER.md`: default and advanced context routing profiles
- `.understand-anything/README.md`: local setup notes
- `.understand-anything/.understandignore`: analysis exclusions
- `docs/agent/SOURCE_UNDERSTANDING.md`: workflow guidance
- `scripts/search_understand_graph.py`: local graph search helper
- `scripts/validate_understand_graph.py`: graph shape validator
- `eval/retrieval/`: Semble retrieval evaluation fixtures

## Public Interfaces
- `semble search "<task>" . --content code`
- `semble search "<task>" . --content all`
- `make code-search QUERY="<task>" CONTENT=all`
- `python scripts/run_agent_tool.py semble search "<task>" . --content all`
- `make ast-grep PATTERN="..." LANG=python`
- `make repomix`
- `.sembleignore`
- `.understand-anything/knowledge-graph.json`
- `make understand`
- `make understand-search`
- `make understand-dashboard`
- `make retrieval-eval`

## Rules
- Do not commit generated graph files unless explicitly agreed.
- Use Semble + `rg` + CODEMAP/module cards as the default retrieval stack.
- Keep Serena optional for symbol-level coding work.
- Treat Repomix as an export tool, not normal daily retrieval.
- Search the graph before broad source scanning.
- Verify graph answers against source files before changing code.
- Keep `.understandignore` aligned with generated and dependency folders.

## Common Tasks
- Install local agent tools: run `make agent-tools-install`.
- Refresh graph: run `make understand`.
- Search code naturally: run `make code-search QUERY="<task>" CONTENT=code`.
- Confirm exact symbols: run `rg "ExactSymbolOrString"`.
- Evaluate retrieval fixtures: run `make retrieval-eval`.
- Search graph: run `make understand-search QUERY="term"`.
- Visual explore: run `make understand-dashboard`.
- Validate graph: run `make validate-understand-graph`.

## Known Pitfalls
- A stale graph can mislead agents after large refactors.
- Generated graph files can become large and noisy in Git.
- Graph search supplements source reads; it does not replace verification.
