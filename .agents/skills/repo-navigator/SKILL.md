---
name: repo-navigator
description: Locate the smallest relevant set of code, tests, documentation, and symbols in an unfamiliar repository. Use for codebase orientation, ownership tracing, implementation discovery, or source questions; remain read-only.
---

# Repository Navigation

1. For non-trivial work, run `python scripts/task_context.py build "<task>"` and review its warnings, gaps, and selected sources.
2. Read `docs/agent/INDEX.md` and confirm the selected route is appropriate.
3. Check the matching codemap or module card and relevant verified memory.
4. Use Semble for natural-language discovery when available, then confirm exact paths and symbols with `rg`.
5. Use Serena only when declarations, references, diagnostics, or refactor-safe symbol information materially helps.
6. Read full files only after retrieval identifies likely targets.
7. Return the context read, candidate files, related tests, exact confirmations, confidence, and unresolved risk.

For knowledge-graph discovery or refresh, read [source-understanding.md](references/source-understanding.md) only when the task needs architecture or dependency relationships. Do not edit files while using this skill.
