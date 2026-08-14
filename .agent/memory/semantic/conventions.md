# Memory: Project Conventions

Type: semantic
Scope: project
Confidence: high
Last verified: 2026-08-07
Source task: .agent/tasks/2026-08-07-plan-evolution-governance.md

## When to use

Use this memory before implementing non-trivial template or code changes.

## Content

- Prefer targeted reads, `rg`, Semble when available, module cards, and deterministic scripts over broad repository scans.
- Make the smallest safe change and update tests or docs when behavior changes.
- Run targeted tests before broad checks.
- Use compressed command output for noisy commands when RTK is available, and rerun raw output only when compressed output is unclear.
- Keep long-term memory concise, reusable, and free of secrets or private data.
- Keep root instructions under the internal byte target and validate agent assets with `make validate-agent-assets`.
- Treat hooks and rules as reviewed defense-in-depth; do not add broad command allow rules for routine checks.
- Before executing a plan or material upgrade, create or update its durable
  record under `.agent/plans/` with strategy, success signals, evidence, and
  user/AI learning. Chat plans are transient coordination only.

## Related files

- `AGENTS.md`
- `docs/agent/CODE_SEARCH.md`
- `docs/agent/COMMAND_OUTPUT_POLICY.md`
- `docs/agent/MEMORY_POLICY.md`
- `docs/agent/CODEX_CUSTOMIZATION.md`
- `.agents/skills/plan-evolution/SKILL.md`
- `.agent/plans/template.md`

## Staleness triggers

- Context retrieval policy changes.
- Command output policy changes.
- New required tools replace the existing default workflow.
- Instruction budgets, skill packaging, or guardrail policy changes.
- Plan-record lifecycle or human-AI learning fields change.
