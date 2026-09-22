# Plan: Routing Token Efficiency

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: upgrade
- Status: completed
- Owners: user and AI
- Version / Relation: v0.5 follow-up to `.agent/plans/completed/2026-09-22-template-reliability-v0-5.md`
- Baseline: uncommitted v0.5 working tree on `ddc2831131c949780b2abc3d966c3f357359286e`; preserve previous implementation.

## Goal

Reduce avoidable reading and orchestration overhead while retaining required
context, source safety, inspectable evidence, and selective independent review.

## Why This Strategy

The local 13-fixture audit found 57,232 proxy tokens across full bundles, with
14,806 in metadata. The login bug fixture loaded 4,468 tokens of unrelated
evaluator tests. The memory index grew from 720 to 3,346 proxy tokens because
machine evidence was mixed with lookup metadata. Fix measured local overhead
before considering an additional model router. These are tokenizer-proxy counts,
not paid usage or evidence of better task success.

## Scope

Tighter deterministic optional-source relevance; compact bounded Markdown reading
views with complete audit output available; compact evidence-aware memory lookup;
reuse guidance and linked bookkeeping; offline-by-default skill-routing evals.
No model calls, automatic memory promotion, weakened review, or new framework.
Keep the current v0.5 version and preserve existing cache identities for full audits.

## Success Signals

- The login-bug fixture excludes unrelated agent-evaluation tests while concrete
  module/symbol requests still retrieve relevant optional sources.
- Compact reading output includes safety warnings, gaps, source identities, and
  required excerpts before optional content, under a complete-output budget.
- Full inspection remains available; large dropped-source lists do not inflate
  default model-readable output.
- Memory lookup reports matching summaries, paths, and current evidence status
  without dumping hashes or changing the memory index schema.
- Default routing evaluation performs no model calls; live runs are explicit.
- Existing checks, focused regressions, install/update checks, and independent
  review pass; before/after context measurements disclose their limits.

## Execution Outline

- [x] Implement and test selection and compact context reading.
- [x] Implement compact memory lookup and focused tests.
- [x] Gate live routing evaluation and clarify reuse/checkpoint workflows.
- [x] Integrate documentation, generated commands, validation, and memory evidence.
- [x] Measure output, run checks and independent review, resolve findings.
- [x] Record outcomes and learning; move this record to completed.

## Decisions And Changes

- 2026-09-23: User authorized improving all audited constraints. Keep required
  sources and safety checks; optimize optional selection and presentation first.
- 2026-09-23: Preserve the original full audit and add a compact Markdown reading
  companion. Budget the complete reading output; fail explicitly when mandatory
  diagnostics and required content cannot fit rather than silently dropping them.
- 2026-09-23: Behavioral reports prefer the compact file per bundle identity with
  a legacy full-only fallback, avoiding double-counting both presentation views.
- 2026-09-23: Independent review exposed that concise checkpoint guidance conflicted
  with the legacy task-log auditor. Support both legacy logs and complete concise
  checkpoints; 11 regressions cover the new form and required resume fields.
- 2026-09-23: Independent context review caught a false-negative for private Python
  symbols. Preserve identifier underscores while tightening ordinary-word relevance.

## Risks And Assumptions

- Stronger filtering can lose useful context; test positive matches and provide
  explicit expansion when a concrete source is missing.
- Compact output must clearly disclose omitted content and preserve errors.
- Context reuse is conditional on task/route/source freshness, not blind cache trust.
- Existing uncommitted v0.5 files are authorized prior work and must be preserved.

## Verification

- `uv run --no-project --with 'pytest>=8,<9' python -m pytest -q`:
  **193 passed, 3 skipped**. Two Windows symlink checks and the unavailable make
  wrapper check are skipped; portable alias checks and direct Python commands pass.
  Includes fresh-install/setup/compact context/memory lookup/offline evaluation
  and update smoke tests with ownership preserved.
- `uv run --no-project python eval/run_eval.py`: all 13 context fixtures with
  complete reading budgets, 20 skill-routing fixtures, 4 hook cases, 6 behavioral
  reference solutions, 8 advisory cases, and asset validation pass.
- `uv run --no-project python scripts/validate_memory_links.py --require-evidence`
  and `uv run --no-project python scripts/audit_memory_staleness.py`: six valid
  cards with unchanged evidence after final source review.
- `uv run --no-project python scripts/audit_task_logs.py`: passes. Concise checkpoint
  compatibility has 11 focused tests; legacy logs remain accepted.
- Configured lint (`python -m compileall -q src scripts eval tests` plus asset
  validation), `python scripts/validate_docs.py`, and `git diff --check` pass.
  The existing typecheck target remains a placeholder.
- Separate independent reviewers covered context, lookup/evaluation integration,
  and root workflow changes. Initial findings were fixed, with one re-review per
  affected scope; no material findings remain. Reviewers did not review their own
  implementation. No live model calls or paid evaluations ran.

## Outcome And Evidence

Delivered all five audited improvements in the existing v0.5 working tree,
preserving prior changes and leaving the work uncommitted. Required sources,
explicit ranges, source safety, manual memory promotion, and selective review
remain in force. The new reading artifact and compact memory view expose omitted
content rather than implying full coverage. Live routing evaluation now requires
`--live --model`; default calls are offline.

Measured the same 13 fixture tasks with search disabled using the `o200k_base`
tokenizer proxy. Baseline full reading output totaled **57,232 tokens**; new default
compact output totaled **31,139**, a **45.59% reduction**. The login-bug fixture fell
from 6,598 to 1,136 tokens, excluding unrelated evaluator tests. Full memory-index
reading was 3,346 tokens in the audit; the new six-card summary/status lookup is
264 tokens. This compares the intended reading surfaces, not identical document
contents or actual model bills. Full audits remain available and require extra
reading when needed. No task-success or billed-cost improvement is claimed.

Ignored detailed reports: `.agent/traces/evals/routing-token-audit-2026-09-22.json`
and `.agent/traces/evals/routing-token-efficiency-2026-09-23.json`. Production has
no tokenizer dependency; the audit used an isolated `uv --with tiktoken==0.12.0`
environment. Memory source review is recorded separately under
`.agent/memory/verification/2026-09-23-token-efficiency.md`.

## Reflection

- What worked: measuring source selection separately from metadata identified
  specific savings. Positive symbol tests and independent review preserved useful
  context while unrelated optional material was removed.
- What did not: initial filtering discarded private identifiers, and concise-log
  guidance initially conflicted with its auditor. Both were fixed with regressions.
  An early full-suite run overlapped edits and observed intermediate failures;
  final checks waited for source freeze.
- User mindset/strategy learning: the user authorized concrete reductions after
  inspecting measured overhead. The implementation retained safety and review
  constraints; no post-release user task outcome is available yet.
- AI workflow/prompt/context learning: distinguish reading views from audit data,
  measure complete rendered output, avoid double-counting companion artifacts,
  synchronize guidance with validators, and coordinate final checks after edits stop.
- Next experiment: measure matched task outcomes after the reading-cost reduction.

## Follow-Up

Keep effectiveness claims separate from token-proxy savings.
