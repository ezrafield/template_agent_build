# Memory: Template Decisions

Type: semantic
Scope: project
Confidence: high
Last verified: 2026-08-02
Source task: .agent/tasks/README.md

## When to use

Use this memory when deciding whether to add dependencies or expand the agent kit.

## Content

- The memory layer is PlugMem-inspired but does not depend on PlugMem.
- The template favors lightweight Markdown, JSON indexes, and deterministic Python scripts over embeddings, graph databases, or model-hosting requirements.
- Memory promotion is manual: scripts can generate candidates, but promoted memory must be reviewed and intentionally indexed.
- Current source code, tests, and docs override memory when they conflict.
- Repository skills inherit the agent-kit version; the template does not maintain a separate skill lockfile.
- Codex is the primary v0.3 runtime, while Claude Code assets remain supported without parity guarantees.
- Fresh clones do not activate project hooks or command rules; users generate and trust them explicitly.

## Related files

- `docs/agent/MEMORY_POLICY.md`
- `docs/agent/MEMORY_PROMOTION_RULES.md`
- `.agent/memory/index.json`
- `docs/adr/0003-codex-agent-system.md`
- `agentkit-manifest.json`

## Staleness triggers

- A real memory engine, embedding index, or graph database is adopted.
- Promotion policy changes from manual to automatic or rule-assisted.
- Template dependency policy changes.
- Runtime priority, skill versioning, or guardrail activation policy changes.
