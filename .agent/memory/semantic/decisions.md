# Memory: Template Decisions

Type: semantic
Scope: project
Confidence: high
Last verified: 2026-09-23
Source task: .agent/tasks/README.md
Verification record: .agent/memory/verification/2026-09-23-token-efficiency.md

## When to use

Use this memory when deciding whether to add dependencies or expand the agent kit.

## Content

- The template favors lightweight Markdown, JSON indexes, and deterministic Python scripts over embeddings, graph databases, or model-hosting requirements.
- Effective task delivery and low maintenance cost drive scope. The reference suite permits at most 49 collected cases; experimental corpora run only by explicit request.
- Memory promotion is manual: scripts can generate candidates, but promoted memory must be reviewed and intentionally indexed.
- Current source code, tests, and docs override memory when they conflict.
- Repository skills inherit the agent-kit version; the template does not maintain a separate skill lockfile.
- Codex is the primary v0.5 runtime, while Claude Code assets remain supported without parity guarantees.
- Fresh clones do not activate project hooks or command rules; users generate and trust them explicitly.
- Task context is persisted as a full Markdown audit plus a bounded compact reading companion, without a JSON sidecar; the JSON route manifest is configuration only.
- Routed requirements are selected before advisory Semble matches, and the compiler re-reads every accepted local line range.
- Missing context, blocked reads, truncation, and unavailable search are warnings; invalid input/configuration and output materialization failures are errors.
- The task-context compiler has no automatic prompt hook.
- Memory source hashes detect drift and require review; they neither establish claim truth nor authorize automatic promotion.

## Related files

- `docs/agent/MEMORY_POLICY.md`
- `docs/agent/MEMORY_PROMOTION_RULES.md`
- `.agent/memory/index.json`
- `docs/adr/0003-codex-agent-system.md`
- `docs/adr/0004-task-context-compiler.md`
- `docs/adr/0005-measurable-reliability.md`
- `docs/agent/context-routes.json`
- `agentkit-manifest.json`
- `docs/agent/AGENTS_AND_SKILLS.md`

## Staleness triggers

- A real memory engine, embedding index, or graph database is adopted.
- Promotion policy changes from manual to automatic or rule-assisted.
- Template dependency policy changes.
- Runtime priority, skill versioning, or guardrail activation policy changes.
- Task-context storage, ordering, search authority, or failure semantics change.
