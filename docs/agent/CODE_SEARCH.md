# Code Search

Use Semble, `rg`, and optional semantic tools as complementary retrieval layers.

## Default Stack

Use by default:
- `docs/agent/CODEMAP.md` for quick module orientation.
- Module cards for ownership, public interfaces, tests, and pitfalls.
- Semble for natural-language source search.
- `rg` for exact symbols, strings, config keys, and paths.

Use optionally:
- Serena for language-server backed symbol navigation, references, diagnostics, and safer refactors.
- ast-grep for structural code patterns.
- Understand Anything for graph and dependency impact analysis.
- Repomix only as an export/bundling tool for external model review.

## Search Order

1. Read `docs/agent/INDEX.md`.
2. Check `.agent/memory/index.json` for relevant semantic or procedural memory.
3. Verify useful memory against current code, tests, and docs.
4. Read `docs/agent/CODEMAP.md` or the relevant module card.
5. Search natural language with Semble:

```bash
semble search "<task>" . --content code
semble search "<task>" . --content all
make code-search QUERY="<task>" CONTENT=all
```

Use `--content code` for implementation tasks. Use `--content all` when docs, tests, config, prompts, or generated context may affect the answer.
When global PATH is not configured, use the project wrapper:

```bash
python scripts/run_agent_tool.py semble search "<task>" . --content all
```

The wrapper sets Semble's index cache to `.agent/context-cache/semble` and Hugging Face model cache to `tools/agent/.hf-cache`; both are ignored. On Windows it also disables Hugging Face symlink caching so Semble works without Developer Mode or administrator privileges.

6. Confirm exact names with `rg`:

```bash
rg "ExactSymbolOrString"
rg --files | rg "module-name|test-name"
```

7. Use Serena when symbol-level behavior matters:
- Find declarations and implementations.
- Find all references.
- Inspect diagnostics.
- Plan safe renames or refactors.

8. Read full files only after retrieval identifies likely targets.

## Decision Matrix

| Situation | Best tool |
| --- | --- |
| "Where is auth handled?" | Semble |
| "Find all places this function is called" | Serena |
| "Search exact env var name" | `rg` |
| "Find React components matching a structure" | ast-grep |
| "Understand repo modules quickly" | `docs/agent/CODEMAP.md` |
| "Analyze dependency impact" | Understand Anything / graph |
| "Send whole repo to external model" | Repomix |
| "Large enterprise monorepo search" | Sourcegraph/Cody |
| "General template default" | Semble + `rg` + CODEMAP |
| "Advanced coding setup" | Semble + Serena + `rg` + CODEMAP |

## Before Editing

Summarize:
- Selected files.
- Why they are relevant.
- Uncertainty or risk.

Then make the smallest safe change and run targeted tests first.
