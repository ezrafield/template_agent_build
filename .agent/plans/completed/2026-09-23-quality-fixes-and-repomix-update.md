# Plan: Quality Fixes and Repomix Update

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: upgrade
- Status: completed
- Owners: user and AI
- Version / Relation: follows `.agent/plans/completed/2026-09-23-documentation-and-quality-audit.md`
- Baseline revision: `8fb85ef62c3b3a25eedf0fa7c8504202e0d0ed6b` plus the uncommitted documentation/CI audit changes

## Goal

Apply the authorized Repomix security update and fix the four concrete quality
gaps identified in the audit, preserving bounded deterministic execution.

## Why This Strategy

Reproduce each failure and add discriminating regression cases before relying on
aggregate scores. Improve existing rules and budgets before introducing services
or model routing. Update only the tool with a confirmed relevant advisory.

## Scope

Repomix manifest/lock and local installation; behavioral fixture graders and
negative mutations; deterministic routing; memory lookup with source paths;
named-symbol excerpt priority; corresponding documentation and verified memory.
Preserve prior uncommitted work, source authority, budget/safety controls, explicit
route overrides, installer ownership, and separate kit/application versions.
No paid live experiments, automatic memory promotion, broad dependency upgrades,
new orchestrator, or new static-analysis framework in this pass.

## Success Signals

- Repomix uses the confirmed fixed release with regenerated lock; local wrapper,
  clean installation, and representative repository packing work.
- Reference solutions pass while seeded plausible incorrect solutions fail.
- Reviewed route paraphrases and mixed intents resolve correctly or expose
  ambiguity; existing context fixtures and explicit overrides remain valid.
- Mixed task prose with POSIX/Windows source paths retains useful memory matches;
  standalone card/directory queries remain precise.
- Requested symbol definitions survive early generic matches within existing
  document/character limits, redaction, and required-source priority.
- Focused and full offline checks pass; independent review has no unresolved
  material findings. Reliability effectiveness remains unmeasured without live data.

## Execution Outline

- [x] Update Repomix and verify installation/export behavior.
- [x] Strengthen graders and add negative-solution regressions.
- [x] Fix route classification and named-symbol context selection; resolve review finding.
- [x] Fix mixed path/prose memory lookup.
- [x] Update docs, review memory evidence, run integrated checks.
- [x] Complete independent review and retrospective.

## Decisions And Changes

- 2026-09-23: User authorized the previously proposed update and four fixes.
  Existing CI prerequisite corrections remain in the working tree.
- 2026-09-23: Divide implementation into isolated file ownership: context engine,
  behavioral evaluation, optional tool update, and root memory/docs integration.
- 2026-09-23: Reproduced six mixed prose/path lookup failures. Preserve precise
  standalone paths (including canonical memory names with spaces), but rank
  lexical task terms when a source path appears in prose. Focused lookup suite:
  38 passed after the fix; original metadata, safety, and output bounds retained.
- 2026-09-23: Negative grader probes confirmed the known invalid documentation
  example and uncovered acceptance of truncated fractional means. Include that
  adjacent correctness gap in the same bounded grader fix.
- 2026-09-23: Optional windows remain in relevance order with accurate source
  ranges, rather than restoring file order: later global clipping must not drop
  the highest-priority definition again. Required/expanded selection is unchanged.
- 2026-09-23: Keep classification schema documentation under a separate H2 so
  everyday bug-fix/general policy slices do not grow by about 1,100 characters.
- 2026-09-23: Integrated suite passed 248 tests, three environment skips; all
  offline evaluations passed. Independent review then found one P2 regression:
  explicit review requests mentioning refactoring silently chose refactor.
  Resolve with bounded review-intent rules and regressions, then one re-review.
- 2026-09-23: Added explicit review/refactor regressions and a review-panel near
  miss. Independent targeted re-review found the P2 resolved; the full final
  suite passed 251 tests. Broader natural-language coverage remains a limitation.

## Risks And Assumptions

- Routing heuristics can overfit small labels; include near-miss and override tests.
- Symbol ranking can starve other context; preserve accurate source ranges and
  hard selection limits after ranking.
- A patched dependency may change its output or transitive compatibility; use
  primary release/advisory evidence and smoke-test actual installed behavior.
- Existing documentation edits are authorized work to retain, not a clean baseline.

## Verification

- Focused lookup: 38 passed. Six new mixed-path queries failed before the fix.
  An initial test-collection string typo was corrected before the failure probe.
- Focused behavioral evaluator: 47 passed. Reproduced invalid `--limit 0` and
  truncated fractional-mean acceptance before strengthening the graders.
- Final focused context: 77 passed, two skips (symlink creation and make absent).
  All six concrete advice-route labels match; existing 13 golden fixtures pass.
- Final full suite: `uv run --no-project --with "pytest>=8,<9" python -m pytest -q`
  reported 251 passed, three environment skips (two symlink, one missing make).
  Includes fresh installation/update, preserved ownership, and installed-kit checks.
- `uv run --no-project python eval/run_eval.py` passed all asset, hook (4), skill
  labels (20), context (13), behavior (6 references and 14 incorrect mutations),
  and advice (8) checks. The context golden evaluation was rerun after the review fix.
- Python compilation, docs validation, and `git diff --check` passed. Lint uses
  compilation plus assets; the existing typecheck placeholder is not counted as
  static typing evidence. No generated document was manually edited.
- Strict memory validation and staleness audit: all six cards unchanged after
  review; updated only eight changed fingerprints across five existing cards.
- Repomix: `npm view repomix@1.18.1 version engines dist.integrity --json`, exact
  package-lock-only update, local and fresh temporary `npm ci`, wrapper versions,
  `npm ls --depth=0`, and synthetic export checks passed. Exports covered README,
  Python source, exclusions, commit history, diffs, and harmless Git-helper
  suppression. No private repository was exported. Temporary workspaces cleaned.
- `npm audit --json --package-lock-only`: zero findings after the update, versus
  seven (four high, three moderate) for the previous lock. Not a full security audit.
- Independent core review found one P2 and no other material issues; the single
  targeted re-review passed after fixes. A different agent independently reviewed
  the package update it did not author and found no material issues.
- Final report review found no material issues; generated COMMANDS.md exactly
  matches its generator. Report links resolve after this plan closure.
- Tool compatibility checks used Windows, Node 24.16.0, npm 11.13.0. Linux, Node
  22, signed-commit GPG behavior, hosted CI, and live model effectiveness remain
  unverified. No paid calls were performed.

## Outcome And Evidence

- Updated exact Repomix 1.16.0 to 1.18.1 for the confirmed upstream advisory:
  https://github.com/yamadashy/repomix/security/advisories/GHSA-4p5g-gh74-q524.
  npm regenerated 35 transitive versions and added one nested package; ast-grep's
  0.44.0 pin and lock records are unchanged. Other direct pins remain intact.
- Graders use protected initial sources for CLI parsing and integrity checks;
  all six cases now have negative mutations that must fail actual acceptance
  checks, not merely scope checks or timeouts. No command text is executed.
- Optional validated manifest intent rules prefer requested workflows over
  incidental domain words, with visible ambiguity/fallback and unchanged explicit
  overrides. Existing manifests without intent rules retain keyword classification.
- Named definitions/identifiers precede generic optional matches; accurate ranges,
  deduplication, redaction, whole-file hashing, and required-source budgets remain.
- Mixed source paths no longer erase task-word matches in memory lookup. Exact
  canonical memory paths, including names with spaces, remain precise.
- Updated README, router/retrieval/evaluation guides, fixture README, version and
  quality reports. Prior documentation and CI prerequisite fixes were preserved.
- Version identities remain agent kit 0.5.0 and separate sample/tool wrapper 0.1.0;
  no release, commit, or push was performed. Earlier token-savings measurement is
  identified as historical rather than remeasured for this follow-up.

## Reflection

- What worked: concrete reproductions guided small fixes; independent review
  caught a request-priority regression despite passing positive route labels.
  Separate package/core reviewers avoided self-review.
- What did not: positive-only grader checks missed both an invalid command and
  fractional truncation; intent precedence initially hid explicit review requests.
- User mindset/strategy learning: the user accepted an evidence-based audit and
  authorized the identified fixes. Observable acceptance cases kept that broad
  request bounded without unrelated tool or framework upgrades.
- AI workflow/prompt/context learning: add negative and near-miss examples, not
  only repaired positives; keep classifier schema details outside everyday
  required slices; preserve ranking through final clipping; state environment
  limits and audit coverage independently of a passing result.
- Next experiment: use the strengthened graders for a separately authorized
  matched live comparison, with scope failures and uncertainty reported first.

## Follow-Up

Hosted CI confirmation requires a later push/rerun. Live reliability and billing
claims require separately authorized matched experiments.
