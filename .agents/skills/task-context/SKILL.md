---
name: task-context
description: Build, explain, or evaluate an inspectable Markdown context bundle for a task. Use when the user explicitly asks what project context applies, why sources were selected, or whether task-context routing is healthy; remain read-only.
---

# Task Context

1. Reuse an inspected current task bundle under `AGENTS.md` freshness rules, or build it with `python scripts/task_context.py build "<task>"`.
2. Read the emitted compact `.read.md` file under `.agent/context-cache/task-context/`; treat source files as authoritative.
3. Review sources, warnings, gaps, omissions, and the complete reading budget. Use `--view full` for the detailed audit only when needed.
4. Use the existing audit to inspect selection. `python scripts/task_context.py explain "<task>"` rebuilds from current sources and may rerun search; use it when a fresh explanation is needed.
5. If a concrete fact is still missing, repeat `--expand-source PATH START END` for the inclusive local ranges needed, with a non-empty `--reason` describing the uncertainty. Supply all ranges on each call; current source is re-read, and prior bundles are never authoritative input.
6. Inspect expansion outcomes, including merged or already included ranges, rejections, clipping, and truncation. Stay within the existing document and character budgets; stop expanding when the fact is resolved or capacity is exhausted.
7. Run `make task-context-eval` when routes or context behavior change.

Required routed sources precede explicit expansion, optional routes, and advisory
Semble suggestions. Expansion cannot displace required excerpts. Missing,
unsafe, truncated, or unavailable optional context is reported as a warning and
does not authorize guessing. This skill does not edit project files or promote
generated bundles into task logs or memory.
