# Optional Source Understanding

Use this reference only when ordinary codemap, module-card, Semble, and `rg`
retrieval cannot answer an architecture, dependency, or onboarding question.

1. Read `docs/agent/SOURCE_UNDERSTANDING.md`.
2. Check whether `.understand-anything/knowledge-graph.json` exists and passes
   `make validate-understand-graph`.
3. Search the graph with `make understand-search QUERY="<task>"`; never load the
   complete graph into context.
4. If the graph is missing or stale after a large refactor, use the installed
   Understand Anything plugin or `make understand` to refresh it.
5. Verify every graph conclusion against current source and tests.

Generated graph files remain uncommitted unless the user explicitly requests
otherwise. Fall back to normal repository navigation when the integration is
not installed.
