---
name: task-context
description: Build, explain, or evaluate an inspectable Markdown context bundle for a task. Use when the user explicitly asks what project context applies, why sources were selected, or whether task-context routing is healthy; remain read-only.
---

# Task Context

1. Build the bundle with `python scripts/task_context.py build "<task>"`.
2. Read the emitted file under `.agent/context-cache/task-context/`; treat source files as authoritative.
3. Review selected and dropped sources, warnings, gaps, hashes, and budget before relying on excerpts.
4. Run `python scripts/task_context.py explain "<task>"` when selection needs inspection without materializing another bundle.
5. Run `make task-context-eval` when routes or context behavior change.

Required and optional routed sources precede advisory Semble suggestions. Missing,
unsafe, truncated, or unavailable optional context is reported as a warning and
does not authorize guessing. This skill does not edit project files or promote
generated bundles into task logs or memory.
