# ADR 0003: Codex-First Agent System

Status: accepted
Date: 2026-08-02

## Context

The v0.2 template had concise project instructions and useful tools, but its 12
repository skill files lacked required frontmatter and therefore were not valid
Codex skills. Size, discovery, installer ownership, hooks, and command rules
also used separate or incomplete checks. The source proposal is retained at
`update/02082026_improve_plan.md`.

## Decision

- Keep repository installation through the existing agent-kit manifest and
  installer; do not add a separate skill lockfile.
- Make Codex the primary v0.3 runtime while preserving Claude Code assets.
- Consolidate the catalog to eight valid, single-purpose skills.
- Enforce internal byte budgets and manifest coverage with one deterministic
  validator.
- Ship hooks and command rules as machine-local opt-in guardrails that require
  explicit generation, review, and Codex trust.
- Keep authenticated skill-routing metrics non-gating until a stable baseline
  exists.

## Consequences

The catalog becomes discoverable and cheaper to route, upgrades can safely
retire recorded kit files with backups, and a fresh clone remains free of active
project hooks and rules. Exact v0.2 skill names listed in the migration guide no
longer activate. Rules remain experimental and are defense-in-depth rather than
a complete security boundary.
