# Plan: Effective Delivery and Minimal Tests

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: strategy
- Status: completed
- Owners: user and AI
- Version / Relation: follows `../completed/2026-09-23-reduce-test-and-doc-duplication.md`; kit 0.5.0
- Baseline: HEAD `8fb85ef62c3b3a25eedf0fa7c8504202e0d0ed6b` plus authorized working changes; 244 collected tests (241 passing, three skips).

## Goal

Prioritize effective task completion with low context, testing, and maintenance
overhead. Keep fewer than 50 collected tests and provide a reusable global skill.

## Why This Strategy

Protect a small set of consequential contracts rather than exhaustively testing
the experimental harness. Count parameterized cases honestly and enforce the
budget so suite growth requires an explicit tradeoff.

## Scope

Add repository/global `test-scope`; prune tests; align default CI, skills, and
existing documentation. Preserve runtime features, safety instructions, installer
ownership, and prior authorized changes. No paid calls or new orchestration service.

## Success Signals

- Full pytest collects at most 49 cases and passes; no hidden legacy test suite.
- Core routing, context safety/budgets, memory, installation, and sample behavior remain covered.
- Skill validates locally and globally; documentation and generated commands agree.
- Experimental evaluations are explicitly optional; no unmeasured effectiveness claims.

## Execution Outline

- [x] Select and prune representative core tests; enforce the collection budget.
- [x] Add skill locally/globally and refocus existing workflow guidance and CI.
- [x] Verify assets, memory, install/update behavior, and independent review.

## Decisions And Changes

- 2026-09-23: The user's new scope supersedes exhaustive v0.5 test coverage.
  Global guidance respects each project's needs; the 49-case cap is template-specific.
- Ordinary CI retains core pytest, compilation and asset checks. Research corpora
  and Codex runtime checks move to manual dispatch; bare Make displays help.
- Removed trivial unit tests made the targeted runner's default empty. Point it
  at the single retained API smoke test and use the current interpreter; preserve
  explicit command arguments and failure exit codes.

## Risks And Assumptions

Pruning removes detailed regression coverage of optional experiments. Retained
offline evaluators remain available explicitly; they are not a hidden default suite.

## Verification

- Full `uv run --no-project --with 'pytest>=8,<9' python -m pytest -q`:
  37 passed in 2.17s; no skips. Focused owner checks passed before integration.
- Isolated collection probe accepts 49 parameterized/skipped cases and rejects
  50 even with ordinary deselection. No removed matrix is hidden in test loops.
- Compilation, asset/docs/module-card validation, strict six-card memory audit,
  skill and advice catalog checks, and diff whitespace checks passed. No paid calls.
- Local/global skill validators passed; both installed files match byte-for-byte.
  Generated COMMANDS is reproducible; CODEMAP refreshed with its generator.
- Fresh install/update preserves project instructions, memory and Makefile;
  ships eleven skills, and leaves host test budgets unchanged. Initial smoke
  wrongly expected merged instruction hashes to match: corrected it to require
  explicit drift for the two affected cards, without refreshing installed memory.
- Targeted-runner smoke passes; explicit failing command retains exit code 7.
- Two independent cross-author review passes found no material findings:
  context/memory coverage and the remaining skill/workflow/CI/installer/test
  changes were reviewed by agents who did not author those files. No re-review
  was needed; no material findings remain.

## Outcome And Evidence

- 244 to 37 collected cases (85% fewer); test modules 13 to 10, lines 2,322 to 828.
- Retained core behavior: context/routing 10, memory 8, installer/assets 8,
  sample API 1, experiment boundaries/hooks 10. Detailed edge matrices removed.
- New portable `test-scope` installed under the user's global Codex skills.
  Kit identity remains 0.5.0; sample application remains 0.1.0.

## Reflection

- User mindset/strategy learning: favor useful outcomes and low maintenance cost.
- What worked: explicit per-area budgets and representative contracts made the
  large reduction reviewable without retaining disguised suites.
- What did not: deleting trivial tests also broke a default command; follow its
  callers and documentation when removing the last test in a directory.
- AI workflow/prompt/context learning: treat validation as a cost justified by
  consequential behavior, not a reason to keep expanding experimental coverage.

## Follow-Up

Live task effectiveness remains unmeasured.
