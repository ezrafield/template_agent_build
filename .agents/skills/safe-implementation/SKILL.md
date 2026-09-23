---
name: safe-implementation
description: Implement a scoped feature, bug fix, or refactor with tests and documentation. Use when the user asks to change code or behavior; do not use for read-only explanation, planning, or review.
---

# Safe Implementation

1. State the goal, observable acceptance criteria, affected modules, and main risk before editing.
2. Reuse the inspected current task bundle under `AGENTS.md` freshness rules; otherwise run `python scripts/task_context.py build "<task>"` for non-trivial work and inspect its compact view.
3. Read only the routed documentation, current implementation, and related tests.
4. Preserve user changes and make the smallest patch that fully satisfies the request.
5. Reuse existing tests where they cover the acceptance criteria. Use `test-scope` when adding or pruning tests: justify each distinct regression, respect the project budget, and avoid new tests for low-impact edits without a meaningful failure mode.
6. Update the smallest durable documentation surface when public behavior, commands, architecture, or contracts change.
7. Run the narrowest relevant test first, then broader lint, type, and regression checks in proportion to risk.
8. For changes spanning multiple modules' behavior or changing a public contract, request an independent read-only review using `code-review`. Give the reviewer the request, acceptance criteria, diff, and verification evidence. Use a separate agent/session where available; disclose same-context review otherwise. Single-file documentation and low-impact edits use normal verification.
9. Fix material findings and perform at most one re-review. Unresolved material findings block a completion claim; report them with evidence rather than continuing an automatic review loop.
10. Report changed files, verification commands, failures or raw reruns, review independence, and remaining risk. Once relevant required checks pass, repeat them only for new changes or unresolved concerns.

Do not add dependencies or change public contracts without explicit justification and synchronized documentation.
