# Memory Retrieval

Use memory after the standard context router and before code search.

## Startup Flow

1. Read `docs/agent/INDEX.md`.
2. Use `python scripts/memory_lookup.py "<task or keyword>"` to find relevant
   semantic or procedural memory without loading the full evidence index. Reuse
   matching metadata already inspected for the current task when it is still current.
3. Read only memory cards that match the task scope or keywords.
4. Lookup checks current source fingerprints for the listed entries. `untracked`
   means none were recorded; `needs-reverification` or `missing-evidence` requires
   current source review. Use `python scripts/audit_memory_staleness.py` when
   age-based staleness or a complete audit matters.
5. Use memory to choose likely files, workflows, tests, and risks.
6. Verify memory with current docs, code, Semble, `rg`, or Serena before editing.
7. Ignore memory that conflicts with current source, tests, specs, or agent docs.

## Retrieval Hints

- Use semantic memory for project facts, conventions, and decisions.
- Use procedural memory for workflows, debugging steps, testing strategy, and refactors.
- Use episodic memory only when a recent task log is directly relevant or a handoff points to it.

## Compact Lookup

```bash
python scripts/memory_lookup.py
python scripts/memory_lookup.py "debugging" --limit 5
python scripts/memory_lookup.py ".agent/memory/procedural/"
```

No query lists concise metadata in index order. Exact IDs take precedence.
Standalone path queries match normalized paths, including legacy Windows
separators. Queries starting with `.agent/memory/` or `memory/` also use path
matching when card or directory names contain spaces. Other queries, including
task prose such as `fix src/api/routes.py error handling`, rank matching words in
IDs, scopes, summaries, keywords, and paths instead of switching to path-only
matching because a source path appears. The same applies to Windows source paths.
Matching is deterministic lexical retrieval, not semantic inference. No match
is reported explicitly; narrow the query when results are omitted by limits.

Each row shows ID, card path, summary, and live evidence status, without source
hashes or card bodies. Statuses come from the existing evidence checker:
`unchanged`, `untracked`, `needs-reverification`, `missing-evidence`, and
`invalid-evidence`. A missing card is also marked. Fingerprint status does not
replace the age-based audit or verify whether a claim is true. The command does
not promote memory, refresh evidence, or change index version 1.

Default output lists at most 10 entries; `--limit` accepts 1–20. Complete Markdown
output is capped at 12,000 characters, with shortened fields and omitted results
disclosed. Queries are limited to 512 characters, index input to 1,000,000 UTF-8
bytes and 1,000 entries, and each lookup to 128 evidence references. Reduce the
limit when evidence work exceeds that bound. Known secret-like values are
redacted before display; keep secrets out of memory rather than relying on a
display filter. Unsafe or malformed metadata fails with an actionable error.

Python integration uses
`render_lookup(root, query="", limit=10, *, index_text=None)` from
`scripts.memory_lookup`. It returns Markdown and raises `MemoryLookupError` on
invalid input. Supply `index_text` when projecting an already-read and hashed
index: the function uses that exact text and does not re-read the index. Evidence
sources are still inspected at lookup time. Full cards and audit records remain
available when their details are needed.

## With Existing Tools

| Tool | Role |
| --- | --- |
| Module cards and CODEMAP | Explain current architecture and ownership |
| Memory | Recall durable lessons from previous work |
| Semble | Find current relevant code snippets |
| `rg` | Confirm exact names, paths, and strings |
| Serena | Check references, declarations, diagnostics, and safe refactors |
| RTK | Compress noisy command output |

Memory should reduce blind searching, not replace verification.
An `unchanged` fingerprint only confirms that a tracked source is unchanged.
It does not verify the meaning, completeness, or applicability of a memory claim.
