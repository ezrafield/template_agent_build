---
name: code-review
description: Perform a read-only review of a diff, branch, or proposed change. Use for merge readiness, regression risk, security, compatibility, and test-gap analysis; do not implement fixes unless the user explicitly asks.
---

# Code Review

1. Identify the request, observable acceptance criteria, exact diff, and verification evidence. Reuse an inspected current `code-review` bundle under `AGENTS.md` freshness rules, or build one with `python scripts/task_context.py build "<task>" --route code-review` for non-trivial reviews.
2. Inspect the relevant diff, surrounding code, routed sources, and context gaps.
3. Check correctness, security, edge cases, compatibility, architecture drift, and test coverage.
4. Verify findings against current source and tests rather than relying on the diff alone.
5. Report findings first, ordered by severity, with file and line, impact, and a concrete fix.
6. Follow with open questions, test gaps, and a short summary.

Prioritize actionable defects over style preferences. State explicitly when no material findings remain.

For implementation review, use an agent/session separate from the implementer
where available and state whether the review was independent. Use a focused brief
and relevant context when the runtime permits scoped handoff. Review actual
artifacts and checks independently of the completion claim. Allow an initial
review and one re-review after fixes; preserve unresolved material findings and
do not declare completion while they remain. Do not invent additional scope or
repeat passing checks without a concrete concern.
