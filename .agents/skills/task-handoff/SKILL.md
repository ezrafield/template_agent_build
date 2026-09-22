---
name: task-handoff
description: Capture concise, reusable state for a multi-step task that is pausing or moving to another agent or session. Use when the user requests a handoff, work must pause, or unresolved state would otherwise be lost.
---

# Task Handoff

1. Create or update the task note under `.agent/tasks/`.
2. Link existing plan goals, assumptions, and verification; record only new state, relevant context, changed files, and checks needed to resume.
3. Include a checkpoint: linked plan, completed acceptance criteria, outstanding findings, verified revision (and dirty-file state), checks/results, and next action. Record external effects already performed so they are not repeated.
4. Include blockers and risks in that checkpoint; avoid repeating the same next action or verification in multiple sections.
5. Keep temporary task state out of semantic and procedural memory until it is reviewed for promotion.

Use factual paths and commands. Keep the handoff concise enough for another agent to resume without rereading the full conversation.
On resume, compare the checkpoint with current files before relying on prior
verification; rerun the smallest affected check when the relevant state changed.
