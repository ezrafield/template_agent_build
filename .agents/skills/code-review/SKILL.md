---
name: code-review
description: Perform a read-only review of a diff, branch, or proposed change. Use for merge readiness, regression risk, security, compatibility, and test-gap analysis; do not implement fixes unless the user explicitly asks.
---

# Code Review

1. Identify the exact review scope and run `python scripts/task_context.py build "<task>" --route code-review` for non-trivial reviews.
2. Inspect the relevant diff, surrounding code, routed sources, and context gaps.
3. Check correctness, security, edge cases, compatibility, architecture drift, and test coverage.
4. Verify findings against current source and tests rather than relying on the diff alone.
5. Report findings first, ordered by severity, with file and line, impact, and a concrete fix.
6. Follow with open questions, test gaps, and a short summary.

Prioritize actionable defects over style preferences. State explicitly when no material findings remain.
