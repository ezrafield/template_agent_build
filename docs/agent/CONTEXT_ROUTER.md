# Context Router

Use this router when a task is more than a one-line command or isolated question.

## Routing Policy

Do not scan the whole repository for non-trivial code tasks. Compile the
smallest inspectable context bundle first, then expand only when uncertainty
remains. `docs/agent/context-routes.json` is the validated machine-readable
route source; `docs/agent/INDEX.md` explains the same routes for humans.

## Standard Route

1. Reuse an already inspected bundle only when the task, route/options, source hashes, and warnings still satisfy `AGENTS.md` freshness guidance; otherwise run `python scripts/task_context.py build "<task>"`.
2. Read the emitted `.read.md` view and review its route, warnings, gaps, source identities, and aggregated drops.
3. Run `python scripts/memory_lookup.py "<task>"` for matching summaries and current evidence status; inspect the raw index only when its metadata needs investigation.
4. Verify useful memory and generated excerpts against current files.
5. Use `rg` for exact confirmation.
6. Use Serena when language-server semantics are valuable.
7. Read full files only after retrieval identifies likely targets.
8. Run targeted tests before broad suites.

Use `explain` to inspect classification without writing a bundle, `--route ID`
for an intentional override, and `--no-search` for reproducible route-only
selection. Routed requirements are selected before explicit expansion, optional
routed sources, and finally Semble suggestions; they cannot be displaced by them.

## Classification Rules

Classification first checks optional manifest `intent_rules` for the requested
workflow, then falls back to weighted trigger phrases. This lets a request to
review a database diff select review context, or a request to repair an API
regression select bug-fix context. A rule is a list of phrase groups: at least
one phrase in every group must match. For example,
`[[["review", "inspect"], ["diff", "patch"]]]` matches either action with either
subject. Rules are literal boundary-aware phrases, not model calls or regular
expressions. Manifests without these rules keep keyword classification.

If several workflows match, or the best keyword scores tie, the bundle and
`explain` disclose the competing route IDs. Weighted trigger score then manifest
order selects one route deterministically; its required sources remain intact.
No matching rule or trigger produces a visible general-context fallback.
Inspect ambiguous or fallback selections before proceeding and use `--route ID`
to choose intentionally. An explicit route bypasses inferred classification.
These rules cover reviewed phrasing, not arbitrary natural-language intent.

## Reading And Audit Views

`build` defaults to `--view compact`: it writes a bounded `<task-hash>.read.md`
reading view alongside the full `<task-hash>.md` audit. `--stdout` prints the
chosen view. Use `--view full` or `explain` when complete selection decisions,
full hashes, or all dropped paths are needed. Existing full-audit filenames and
the source-hashing rules remain unchanged; neither artifact is authoritative.
A full-only rebuild removes an older reading companion rather than leaving it
apparently current; the next compact build recreates it from current source.

The compact limit covers the **entire rendered Markdown**, including warnings,
gaps, provenance, and headings. Each source has one path/range/hash-prefix
identity; drop reasons are counted rather than expanded into a long table.
Required and explicitly expanded excerpts take precedence. Optional excerpts
that do not fit are visibly clipped or omitted. If required content and
diagnostics cannot fit, the command fails explicitly and leaves the full audit
available; it does not silently discard required guidance. Full audits limit
excerpt characters and can exceed the complete reading-view budget.

The memory index receives a compact summary/path/current-evidence-status
projection derived from the exact text whose source hash was captured. Raw
index fields and evidence hashes remain in the full audit. Projection omissions
or shortened summaries are disclosed; verify relevant cards against source.

Optional relevance ignores generic workflow words such as "fix", "failing",
"regression", and "test". Concrete paths, module names, and named symbols retain
priority; body-only matches need multiple informative task terms. Large optional
files use relevant line windows bounded to 100 lines and 6,000 excerpt characters.
Named definitions come first, then explicit identifier matches, then ordinary
word matches. Windows retain relevance order, merge adjacent selected lines,
and exclude overlaps; consult their displayed source ranges rather than assuming
the excerpt follows file order. This keeps a later named function ahead of early
generic comments when capacity runs out. Hashes still cover the complete original
file, and redaction and required-source priority are unchanged. A window is
navigation context; request explicit expansion for additional implementation
details instead of assuming omitted lines are irrelevant.

## Bounded Expansion

When a specific fact is missing, request inclusive line ranges with a reason:

```bash
python scripts/task_context.py build "<task>" --expand-source src/example.py 20 45 --expand-source docs/specs/example.md 5 18 --reason "Resolve validation behavior and its contract"
```

`explain` accepts the same flags without writing a bundle. Supply every desired
range on each call: the compiler reads current local files, never an earlier
bundle. A non-empty `--reason` is required. Paths must be repository-relative;
containment, secret-file blocking, exclusions, and redaction still apply. Keep
credentials out of task text and reasons even though known secret-like patterns
are redacted before rendering.

Requests use caller path order, merge overlapping or adjacent ranges, and count
each normalized path once. Additional lines append after required excerpts from
the same file without repeating already included lines. Explicit requests use
remaining capacity before optional routed and search content; the 10-document
and 40,000-character limits remain in force. Invalid or unavailable ranges are
reported, ranges beyond the end of a file are clipped with a warning, and budget
truncation never removes an already selected required excerpt. Inspect the
expansion trace and warnings before relying on the result.

Expanded bundle names include normalized requests and the redacted reason in
their cache identity. Builds without expansion keep their existing task hash.
Bundles remain disposable Markdown; there is no automatic retrieval loop or
structured cache sidecar.

## Tool Profiles

### Default

Use the task-context bundle + `rg` + CODEMAP/module cards.

This profile has low setup cost, low token cost, high portability, and works well across Codex, Claude Code, Cursor, and similar agents.

### Advanced Coding

Use the task-context bundle + Serena + `rg` + CODEMAP/module cards.

Enable this profile for serious Python, TypeScript, Java, C#, and Go projects where references, declarations, diagnostics, and refactors benefit from language-server semantics.

### Export

Use Repomix only when the task requires sending a bundled repository snapshot to an external model or reviewer. It should not be the default daily retrieval workflow.

## Escalation Signals

Let the compiler append advisory Semble context when:
- The task is phrased in product or behavior language.
- You do not know the exact symbol name.
- Relevant files could span docs, config, tests, and source.

Escalate from Semble or `rg` to Serena when:
- You must identify all references.
- A rename or refactor crosses files.
- Diagnostics or type-aware symbol information affects correctness.

Escalate to graph tools when:
- Dependency impact matters.
- You need architecture-level relationships.
- The task is onboarding, review, or broad source understanding.
