# CLAUDE.md

Use this project as an agent-native codebase.

## Start Here
For every non-trivial task:
1. Read `docs/agent/INDEX.md`.
2. Check `.agent/memory/index.json` for relevant semantic or procedural memory.
3. Verify memory against current code, tests, and docs before relying on it.
4. Read the relevant module card.
5. Create or update a task note in `.agent/tasks/` if the task has more than one step.
6. Use `.agent/plans/template.md` for complex or multi-phase work.

## Token-Saving Behavior
- Do not explore unrelated directories.
- Use Semble for natural-language code search before reading many files. Prefer `make code-search QUERY="..." CONTENT=all` when relying on project-local tools.
- Use `rg` for exact symbol and string confirmation.
- Use Serena only when symbol references, declarations, implementations, diagnostics, or safe refactors require language-server semantics.
- Use compressed command output for noisy commands when RTK is available.
- Prefer targeted reads over broad scans.
- Summarize findings before expanding scope.

## Long-Term Memory
- `.agent/memory/semantic/` stores stable facts, conventions, and decisions.
- `.agent/memory/procedural/` stores reusable workflows.
- `.agent/tasks/` stores episodic task logs.
- Memory is a decision aid; current repository files are authoritative.
- Generated memory candidates require manual promotion.

## Command Output
- Prefer RTK for noisy commands such as `git status`, `git diff`, tests, lint, typecheck, search, and logs.
- Use `make git-status`, `make git-diff`, and compact make targets to prefer workspace-local RTK with raw fallback.
- If compressed output is unclear, rerun the smallest relevant command in raw mode.
- Do not hide failures; preserve exit codes, stack traces, failed assertions, and actionable errors.

## Safety
- Never delete files, rewrite migrations, rotate secrets, or change production config without explicit approval.
- Prefer small patches.
- Run targeted tests first.

## Final Response Format
- Summary
- Files changed
- Tests or commands run
- Risks or follow-up
