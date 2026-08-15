---
name: safe-implementation
description: Implement a scoped feature, bug fix, or refactor with tests and documentation. Use when the user asks to change code or behavior; do not use for read-only explanation, planning, or review.
---

# Safe Implementation

1. Restate the goal, success criteria, affected modules, and main risk.
2. For non-trivial work, run `python scripts/task_context.py build "<task>"` and review its warnings, gaps, and selected sources.
3. Read only the routed documentation, current implementation, and related tests.
4. Preserve user changes and make the smallest patch that fully satisfies the request.
5. Add or update tests whenever behavior changes.
6. Update the smallest durable documentation surface when public behavior, commands, architecture, or contracts change.
7. Run the narrowest relevant test first, then broader lint, type, and regression checks in proportion to risk.
8. Report changed files, verification commands, failures or raw reruns, and remaining risk.

Do not add dependencies or change public contracts without explicit justification and synchronized documentation.
