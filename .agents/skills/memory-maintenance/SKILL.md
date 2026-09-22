---
name: memory-maintenance
description: Review, promote, validate, or retire project semantic and procedural memory. Use when durable lessons should move from task notes into `.agent/memory/`, or when memory links and staleness need auditing.
---

# Memory Maintenance

1. Reuse an inspected current `memory-maintenance` bundle under `AGENTS.md` freshness rules, or run `python scripts/task_context.py build "<task>" --route memory-maintenance` and inspect its compact view.
2. Read `docs/agent/MEMORY_POLICY.md`, `MEMORY_RETRIEVAL.md`, and `MEMORY_PROMOTION_RULES.md`.
3. Keep raw episodic state in `.agent/tasks/`; generate a candidate with `make extract-task-memory TASK=<path>` when useful.
4. Verify every proposed fact against current code, tests, and documentation.
5. Remove secrets, personal data, transient failures, and unsupported conclusions.
6. Promote only concise reusable facts or procedures. For newly promoted or re-verified entries, capture reviewed source fingerprints with `python scripts/memory_evidence.py <source-path> ...`, then update `.agent/memory/index.json` and synchronized verification dates.
7. Preserve original task provenance; link a separate verification record for a later review when needed. Generated candidates and captured hashes do not by themselves verify a claim.
8. Run `python scripts/validate_memory_links.py --require-evidence <memory-id>` and `make audit-memory`. Report unchanged, untracked, needs-reverification, missing-evidence, or invalid-evidence states; inspect changed sources before refreshing hashes.

Treat memory as guidance, never authority. Prefer retiring stale content over preserving misleading history.
