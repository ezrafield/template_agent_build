# Context Router

Use this router when a task is more than a one-line command or isolated question.

## Routing Policy

Do not scan the whole repository for non-trivial code tasks. Compile the
smallest inspectable context bundle first, then expand only when uncertainty
remains. `docs/agent/context-routes.json` is the validated machine-readable
route source; `docs/agent/INDEX.md` explains the same routes for humans.

## Standard Route

1. Run `python scripts/task_context.py build "<task>"`.
2. Review its route, warnings, gaps, hashes, selected sources, and dropped-source reasons.
3. Check `.agent/memory/index.json` for additional relevant memory.
4. Verify useful memory and generated excerpts against current files.
5. Use `rg` for exact confirmation.
6. Use Serena when language-server semantics are valuable.
7. Read full files only after retrieval identifies likely targets.
8. Run targeted tests before broad suites.

Use `explain` to inspect classification without writing a bundle, `--route ID`
for an intentional override, and `--no-search` for reproducible route-only
selection. Routed requirements are selected before optional or Semble sources
and cannot be displaced by them.

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
