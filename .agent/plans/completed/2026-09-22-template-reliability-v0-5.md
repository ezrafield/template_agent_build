# Plan: v0.5 Measurable Reliability and Optional Jev Experiments

## Metadata

- Created: 2026-09-22
- Updated: 2026-09-22
- Kind: upgrade
- Status: completed
- Owners: user and AI
- Version / Relation: v0.5.0; successor to `.agent/plans/completed/2026-08-15-task-context-compiler-v0-4.md`
- Baseline revision: `ddc2831131c949780b2abc3d966c3f357359286e`

## Goal

Deliver behavioral evaluations, evidence-backed memory, bounded context expansion,
independent review, and an optional Jev shadow experiment. Correct task completion
is primary; cost, latency, and context size are secondary measurements.

## Why This Strategy

Measure actual task outcomes before changing model-driven defaults. Preserve the
stdlib Python/Markdown architecture and deterministic controls while adding
inspectable evidence and optional experiments. Research motivates mechanisms,
not a claim that this template already improves agent performance.

Sources:
- https://docs.typesafe.ai/introduction
- https://docs.typesafe.ai/models
- https://arxiv.org/abs/2608.11888
- https://www.letta.com/blog/evaluating-memory-in-production-agents/
- https://arxiv.org/abs/2512.24601
- https://www.anthropic.com/engineering/harness-design-long-running-apps

## Scope

Six evaluator-owned behavioral fixtures and opt-in matched live runs; backward-
compatible memory evidence; explicit line-range expansion under existing budgets;
selective independent review and handoff checkpoints; stdlib Jev adapter used only
for shadow measurements; v0.5 packaging, docs, validation, and installed-project tests.
No new framework, database, active model routing, automatic memory promotion,
automatic retrieval loop, or paid model calls in CI. Sample app version stays unchanged.

## Success Signals

- Existing 13 context and 20 skill-routing fixtures remain valid.
- Offline tests cover grading, isolation, timeouts, evidence drift, expansion,
  advisory failures, and unchanged deterministic execution.
- Full suite, lint, asset validation, memory audits, and install/update checks pass.
- Live experiments require explicit invocation, use bounded workspaces/timeouts,
  report unsuccessful trials, and make unavailable metrics explicit.
- Effectiveness stays **not yet measured** unless matched live results exist.

## Execution Outline

- [x] Build behavior fixtures, evaluator, and skill-routing failure accounting.
- [x] Add memory evidence and re-verify bundled cards without invented provenance.
- [x] Add explicit bounded context expansion with stable default behavior.
- [x] Update independent review and checkpoint workflows.
- [x] Implement and test optional Jev shadow advice and labeled evaluation.
- [x] Integrate manifest, installer, setup generation, docs, ADRs, and CI for v0.5.0.
- [x] Run checks, independent review, fixes, and at most one re-review.
- [x] Record outcomes and learning; move this record to completed.

## Decisions And Changes

- 2026-09-22 — User chose broader v0.5, reliability first, and optional Jev shadow experiments.
- 2026-09-22 — Captured clean v0.4 baseline before implementation. Agent-kit version
  changes independently from the sample application's version.
- 2026-09-22 — Fresh-install tests exposed that project-local exclusions also
  removed nested fixture src/spec folders. Root-anchor ownership patterns while
  preserving recursive runtime/cache exclusions; regression and install tests pass.
- 2026-09-22 — Initial independent review found that caller-created route catalog
  descriptions bypassed outbound redaction. Redact at the transport boundary and
  test task, route, and skill markers together.
- 2026-09-22 — Independent review also found legacy Windows metadata paths were
  rejected by the new evidence path policy. Normalize legacy metadata separators
  without relaxing the new evidence schema; preserve older date/source metadata
  compatibility for untracked entries and add regression coverage.
- 2026-09-22 — Independent context review found false coverage after truncation,
  sensitive path text in output, and alias targets bypassing source exclusions.
  Preserve only confirmed range coverage, redact rendered paths and warnings,
  and recheck resolved targets before reading; portable regression tests cover all three.
- 2026-09-22 — Separate reviewers completed one re-review of the corrected areas.
  No material code findings remained. Reviewed the final manifest against both
  affected memory cards, refreshed their evidence, and passed the strict audit.

## Risks And Assumptions

- Live model access is optional; tests use fake runners/transports and incur no model charges.
- Evidence hashes detect drift, not whether a memory claim is false.
- Explicit expansion cannot displace required excerpts or exceed existing budgets.
- Jev never controls routing, permissions, context expansion, or completion checks.
- Preserve installer-owned versus project-owned file boundaries and legacy memory entries.

## Verification

Verified the uncommitted v0.5 working tree based on baseline
`ddc2831131c949780b2abc3d966c3f357359286e`. No release commit or tag was created.

- `uv run --no-project --with 'pytest>=8,<9' python -m pytest -q`:
  **122 passed, 3 skipped**. The skips are native symlink checks on Windows (two)
  and the make wrapper check (make is unavailable). Portable alias-path
  regression checks pass. Includes real-manifest fresh-install/setup/offline-eval
  and update smoke checks, ownership, backup, and pruning coverage.
- `uv run --no-project python eval/run_eval.py`: asset validation, 4 hook cases,
  20 skill-routing fixtures, 13 context goldens, 6 behavioral reference solutions
  with failing initial states, and 8 advisory label cases all pass.
- `uv run --no-project python -m compileall -q src scripts eval tests`: passes;
  together with asset validation, this is the repository's configured lint check.
  The existing typecheck target is a placeholder, not an executed type checker.
- `uv run --no-project python scripts/validate_memory_links.py --require-evidence`
  and `uv run --no-project python scripts/audit_memory_staleness.py`: all six
  cards valid with unchanged evidence after final source review.
- `uv run --no-project python scripts/validate_docs.py` and
  `uv run --no-project python scripts/validate_agent_docs.py`: pass, with zero
  asset errors or warnings. `git diff --check` passes.
- Independent initial reviews plus one re-review per assigned scope completed
  in separate agents. Reviewers inspected areas outside their implementation
  ownership. All material findings are resolved; no further automatic review loop.

## Outcome And Evidence

Delivered all five capabilities and agent-kit v0.5.0 packaging, documentation,
generators, and CI integration. The sample application stays at 0.1.0 and memory
index stays at version 1. Existing user-memory ownership and default context
identities remain compatible. Generated command documentation was regenerated
from the setup generator. Live effectiveness: **not yet measured**. No paid/live
model calls ran, and offline fixture success does not establish reliability gains.

## Reflection

- What worked: bounded parallel implementation, evaluator-owned reference checks,
  real install smoke tests, and independent review exposed concrete integration
  and safety regressions before release completion.
- What did not: recursive ownership exclusions initially removed fixture sources;
  initial redaction and path checks missed custom catalogs and resolved aliases.
  New regression tests preserve the corrected behavior.
- User mindset/strategy learning: the user's selected scope prioritized measured
  task completion and opt-in experiments. That choice supported shipping useful
  infrastructure without claiming unobserved improvement or enabling active advice.
  No post-release user outcome is available yet.
- AI workflow/prompt/context learning: test installed assets as well as the source
  tree; enforce redaction at serialization boundaries; distinguish legacy metadata
  from stricter additive evidence; track retained context separately from requested
  ranges; review changed sources before refreshing fingerprints.
- Next experiment: matched optional live comparisons against the captured baseline.

## Follow-Up

Keep Jev in shadow mode. Any later active routing or orchestration upgrade needs
a linked successor plan and evidence from matched evaluations.
