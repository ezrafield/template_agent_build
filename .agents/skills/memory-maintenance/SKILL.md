---
name: memory-maintenance
description: Review, promote, validate, or retire project semantic and procedural memory. Use when durable lessons should move from task notes into `.agent/memory/`, or when memory links and staleness need auditing.
---

# Memory Maintenance

1. Read `docs/agent/MEMORY_POLICY.md`, `MEMORY_RETRIEVAL.md`, and `MEMORY_PROMOTION_RULES.md`.
2. Keep raw episodic state in `.agent/tasks/`; generate a candidate with `make extract-task-memory TASK=<path>` when useful.
3. Verify every proposed fact against current code, tests, and documentation.
4. Remove secrets, personal data, transient failures, and unsupported conclusions.
5. Promote only concise reusable facts or procedures, then update `.agent/memory/index.json`.
6. Run `make audit-memory` and report staleness or broken links.

Treat memory as guidance, never authority. Prefer retiring stale content over preserving misleading history.
