---
name: plan-evolution
description: Create, update, close, and review durable plan records under `.agent/plans/`. Use for plans, roadmaps, strategies, upgrades, migrations, version changes, multi-step execution plans, or retrospective comparison of assumptions and outcomes to improve human-AI collaboration.
---

# Plan Evolution

Make the plan file the durable learning record. Chat plans and planning tools
may coordinate execution, but they do not replace the file.

## Workflow

1. Search `.agent/plans/{active,backlog,completed}/` for an existing record.
2. Before substantive execution, create a missing record from
   `.agent/plans/template.md`. Use `YYYY-MM-DD-short-name.md` in `active/`, or
   `backlog/` when execution is intentionally deferred.
3. Fill the goal, scope, testable strategy hypothesis, success signals, risks,
   and execution outline. Record concise decision rationale; never record hidden
   chain-of-thought, secrets, or private data.
4. Keep the same file current as assumptions, scope, decisions, or evidence
   change. Append dated changes instead of rewriting history.
5. At closure, compare outcomes with success signals, complete both user and AI
   learning prompts, set the final status, and move the file to `completed/`.
   Use `superseded` or `abandoned` honestly when applicable.
6. For a later strategy or version, create a new linked record instead of
   overwriting the old one. Put cross-plan synthesis in `reports/`.

## Required Boundaries

- Create a record for every explicit plan and every material version upgrade,
  including upgrades to product behavior, architecture, agent workflows,
  prompts, models, or collaboration strategy.
- Also create a record when execution adopts a multi-step plan even if the user
  did not use the word "plan".
- Do not create one for a direct read-only answer or an unplanned one-step
  action.
- Keep task logs, ADRs, and memory in their existing roles; link them when
  useful, but do not use them as substitutes for the plan record.
