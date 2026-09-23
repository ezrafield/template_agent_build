# Plan: Reduce Test and Documentation Duplication

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: plan
- Status: completed
- Owners: user and AI
- Version / Relation: follows `2026-09-23-quality-fixes-and-repomix-update.md`
- Baseline: current uncommitted working tree; 251 passing tests, three skips.

## Goal

Reduce repeated checks and prose while retaining useful behavior coverage and
one authoritative explanation per topic.

## Why This Strategy

Remove duplication based on the failure or reader need it covers, rather than
reducing counts arbitrarily. Existing plans already retain historical evidence.

## Scope

Audit overlapping tests, fixture validation, evaluation guides, and recent audit
documents. Consolidate clear duplicates; preserve safety, installer ownership,
recent defect regressions, manual memory review, and existing user changes.
No runtime feature removal, dependency changes, or paid calls.

## Success Signals

- Fewer repeated test executions and less operational documentation.
- Every removed check maps to retained coverage; public commands remain usable.
- Docs links, generated-document ownership, memory evidence, and checks remain valid.

## Execution Outline

- [x] Consolidate duplicate tests and evaluation checks.
- [x] Reduce repeated documentation and historical audit prose.
- [x] Verify coverage, links, memory, and independent review.

## Decisions And Changes

- 2026-09-23: User requested less test/document overhead. Keep this record short;
  use counts and links instead of another narrative audit report.
- Tests: remove duplicate positive/invalid rows and repeated real grading; keep
  distinct boundaries. CI runs pytest only in test.yml and assets only in the
  agent job; one ownership guard rejects an application-only test subset.
- Docs: remove duplicate QUALITY_AUDIT (history is already in completed plans),
  shorten versions/README, and generate one command list with links to details.
- Independent docs review caught a checkout-only aggregate command in generated
  installed-kit guidance. Replaced it with a shipped runner and clarified scope.

## Risks And Assumptions

Similar-looking cases may protect distinct boundaries; retain those distinctions.

## Verification

- Full pytest: 241 passed, three unchanged environment skips; focused installer/
  asset checks: 11 passed. All offline evaluations, compilation, asset/docs
  validation, six-card strict memory audit, and diff checks passed.
- Generated COMMANDS is reproducible; all retained documentation links resolve.
  Independent test/CI/generator review found no material findings.
- The documentation P2 passed one targeted re-review; final fresh-install/update
  smoke passed after correction. No unresolved material findings remain.

## Outcome And Evidence

- Six selected docs: 5,247 to 2,402 words (-54.2%); one duplicate report removed.
- Eleven duplicate cases removed, one CI-ownership guard added: net ten fewer.
  Behavior tests avoid an estimated 16 repeated real-grading subprocesses.
- Retained coverage: 14 real negative mutations now also check isolation and
  diagnostics; generic intent test covers ties; shared renderer/definition cases
  cover redaction, provenance and limits; uppercase ID case covers exact matching.
- CI retains full pytest in test.yml and asset validation in agent-doc-check;
  removes their duplicate runs. No application, routing, memory, or eval feature removed.

## Reflection

- What worked: mapping each removal to retained coverage identified safe savings.
- What did not: overlapping reports and independently added regressions repeated
  evidence; the CI validator initially assumed a duplicated test job.
- User mindset/strategy learning: the user values low maintenance overhead as
  well as reliability; preserve boundaries without expanding counts for their own sake.
- AI workflow/prompt/context learning: link canonical guidance and reuse costly
  test executions; document measured reductions without assuming runtime savings.
- Next experiment: measure maintained coverage, not test-count growth.

## Follow-Up

Live effectiveness and hosted CI remain separate from this local cleanup.
