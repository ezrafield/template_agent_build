# ADR 0004: Markdown Task-Context Compiler

Status: accepted
Date: 2026-08-15

## Context

The v0.3 agent kit routes agents through `docs/agent/INDEX.md`, memory, module
cards, and optional search, but it does not record which sources were selected,
dropped, missing, truncated, or unsafe for a specific task. Retrieval tests also
measure Semble results rather than the complete routed context workflow.

## Decision

- Add a Python-stdlib task-context compiler backed by a validated JSON route
  manifest and documented by `docs/agent/INDEX.md`.
- Materialize only an ignored Markdown bundle. Keep structured build state in
  memory for explanation and deterministic evaluation; do not persist a JSON
  artifact sidecar.
- Select required and optional routed sources before optional Semble results.
  Search may fill spare budget but cannot evict routed context.
- Limit excerpt content to 10 documents and 40,000 characters, record SHA-256
  source hashes, and explain every selected or dropped candidate.
- Reject unsafe reads and redact conservative inline secret patterns. Surface
  missing, unsafe, truncated, and unavailable-search conditions as warnings so
  a partial bundle remains usable.
- Expose explicit CLI and Make targets plus a discoverable `task-context` skill;
  do not add automatic prompt hooks or prompt logging.

## Options Considered

1. Parse `INDEX.md` directly. This avoids a configuration file but makes normal
   documentation edits an unstable runtime interface.
2. Make semantic search authoritative. This improves free-form recall but makes
   the baseline depend on optional tooling and weakens deterministic evaluation.
3. Adopt or vendor `contextd`. This provides a broader build system but adds
   workspace, pack, adapter, and artifact concepts outside this template's
   lightweight scope.

The selected design keeps the existing router authoritative while adding the
smallest inspectable build and evaluation layer.

## Consequences

Task preparation becomes auditable and golden-testable, source drift is visible
through hashes, and the workflow still works without Semble. Route metadata and
`INDEX.md` become synchronized public agent-kit interfaces. Markdown is easy to
inspect but intentionally not a durable machine-readable artifact; consumers
that need structured state must invoke the compiler rather than parse bundles.
