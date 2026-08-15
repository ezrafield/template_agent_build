---
name: architecture-decision
description: Compare consequential technical options and record a durable decision. Use for dependency, database, infrastructure, service-boundary, retrieval, or agent-architecture choices; do not use for routine local edits.
---

# Architecture Decision

1. Run `python scripts/task_context.py build "<task>" --route architecture-decision` and review its gaps.
2. State the decision, constraints, non-goals, and compatibility requirements.
3. Compare two or three practical options against those constraints.
4. Recommend the simplest option that satisfies the requirements.
5. Identify migration cost, reversibility, operational risk, and follow-up work.
6. Create or update an ADR when the decision changes durable project behavior.

Return the decision, options considered, recommendation, tradeoffs, and ADR status. Prefer the existing architecture unless a concrete constraint requires change.
