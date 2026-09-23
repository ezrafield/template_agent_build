# Plan: Documentation and Component Quality Audit

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: plan
- Status: completed
- Owners: user and AI
- Version / Relation: v0.5 documentation follow-up to `.agent/plans/completed/2026-09-23-routing-token-efficiency.md`
- Baseline revision: `8fb85ef62c3b3a25eedf0fa7c8504202e0d0ed6b`

## Goal

Make onboarding accurate and concise, align affected guides with implemented
behavior, and provide an evidence-based assessment of component versions,
quality, and the next useful optimizations.

## Why This Strategy

The documentation audit found outdated workflow instructions, incomplete memory
promotion guidance, and optional tooling in the default quickstart. Separate
core use from optional integrations, retain one authoritative explanation per
topic, and assess version freshness separately from tested compatibility.

## Scope

Rewrite README and affected guides; verify documented commands; inspect pinned,
installed, and current upstream component versions when observable; assess tests
and implementation gaps; rank concrete improvements. Preserve dependency pins,
runtime behavior, safety, memory ownership, and generated-document workflow.
No paid model calls or dependency upgrades are implied by the audit.

## Success Signals

- README starts with a working minimal setup and links to optional tool details.
- Instructions consistently describe compact context, conditional reuse,
  evidence-backed memory, and offline-by-default evaluation.
- Version report identifies provenance/date, mismatches, unknowns, and tested
  compatibility without assuming the newest version is the best upgrade.
- Quality findings identify evidence, impact, and bounded next actions.
- Relevant checks and independent documentation review pass; changed memory
  evidence is re-verified deliberately.

## Execution Outline

- [x] Rewrite README and correct affected guides.
- [x] Audit component versions against local files and primary upstream sources.
- [x] Audit quality and prioritize further improvements.
- [x] Verify commands, generated docs, install coverage, and memory evidence.
- [x] Review results, record outcomes and learning, and close this plan.

## Decisions And Changes

- 2026-09-23: User requested documentation implementation plus ideas and version/
  quality checks. This is a documentation and audit change; dependency upgrades
  and new orchestration behavior remain follow-up proposals.
- 2026-09-23: Actual GitHub runs for the baseline failed: agent-doc-check lacked
  pytest, and the test job lacked required rg. Extend this pass only to explicit
  CI prerequisite installation; retain dependency pins and runtime behavior.
- 2026-09-23: Primary upstream evidence identifies a Repomix advisory affecting
  the current optional-tool pin. Document its specific trigger and a bounded
  upgrade recommendation; do not perform an untested dependency update.

## Risks And Assumptions

- Upstream release metadata may be incomplete; label unverified versions instead
  of inferring an upgrade from dates alone.
- README commands must distinguish the template checkout from an installed kit.
- Keep generated documentation changes in its generator, and existing project
  memory intact while refreshing reviewed source evidence.

## Verification

- Focused installer and asset suite: 10 passed, including fresh installation,
  update, ownership rules, and installed-kit checks.
- Full suite via `uv run --no-project --with "pytest>=8,<9" python -m pytest -q`:
  193 passed, two symlink skips and one skip because make was unavailable.
- `eval/run_eval.py`: 13 context fixtures, 20 skill labels, four hook cases,
  six behavioral fixtures/reference solutions, eight advice labels, and asset
  validation passed. No paid or authenticated model calls.
- `validate_docs.py`, `validate_agent_docs.py`, Python compilation, and
  `git diff --check` passed. Generated COMMANDS.md matched its generator exactly;
  no generated document was manually edited.
- README context-build and memory-lookup commands succeeded; optional make was
  unavailable locally, so Python checks used `uv run --no-project python`.
- Strict evidence validation and staleness audit: all six memory cards unchanged
  after reviewing the affected project-facts/debugging-playbooks INDEX claims.
  Refreshed only those two source fingerprints; kept historical provenance.
- Independent reviewer found no material issues in README, quality report, and
  CI corrections; also checked actual hosted failures and local report links.
- CI workflow prerequisites are corrected locally. Updated workflows have not
  run on GitHub yet; hosted confirmation is explicitly outstanding.

## Outcome And Evidence

- Rewrote README around core onboarding, installation ownership, compact context,
  manual evidence, evaluation limits, and optional integrations. Aligned INDEX,
  SOURCE_UNDERSTANDING, and TOOLS with current behavior.
- Added dated `docs/agent/COMPONENT_VERSIONS.md` distinguishing declared, locked,
  installed, and upstream versions. Agent kit remains 0.5.0; sample application
  and tool wrapper retain their separate 0.1.0 identities. Pins are unchanged.
- Added `docs/agent/QUALITY_AUDIT.md` with reproducible gaps and acceptance ideas:
  grader discrimination, ambiguous routing, mixed prose/path memory lookup,
  named-symbol excerpt priority, and stronger static checks.
- Hosted baseline runs revealed missing pytest and rg prerequisites:
  https://github.com/ezrafield/template_agent_build/actions/runs/35769449424
  and https://github.com/ezrafield/template_agent_build/actions/runs/35769449380.
  Added declared dev dependencies to the agent job and ripgrep to both test jobs.
- Primary Repomix advisory places the optional 1.16.0 pin in its affected range:
  https://github.com/yamadashy/repomix/security/advisories/GHSA-4p5g-gh74-q524.
  Both reports describe the crafted Git-metadata trigger, fixed 1.18.1 release,
  and bounded upgrade follow-up. No dependency update was performed.
- Live task reliability remains not yet measured. Earlier context-token proxy
  savings are reported with their scope, without inferring success or billing.

## Reflection

- What worked: parallel documentation, local-quality, and primary-source version
  audits found distinct gaps; a separate review checked the final representations.
- What did not: local passing tests had masked hosted prerequisite failures;
  positive reference-solution checks also missed a plausible wrong solution.
- User mindset/strategy learning: the user's request connected concise onboarding
  with component quality. The result makes operational prerequisites and measured
  evidence visible together, rather than treating documentation as cosmetic.
- AI workflow/prompt/context learning: inspect hosted runs before declaring CI
  health; treat pinned, installed, current, and tested versions as separate facts;
  review changed source meaning before updating memory fingerprints.
- Next experiment: apply the focused Repomix security update, then seed incorrect
  fixture solutions before spending on matched live reliability comparisons.

## Follow-Up

Keep measured reading-cost reduction separate from unmeasured live task success.
Prioritize the affected optional-tool update, then the bounded improvements in
QUALITY_AUDIT.md. Hosted CI requires a subsequent push/rerun. This documentation
task closes with those follow-ups visible; it does not claim they were implemented.

2026-09-23 cleanup: the later quality-fixes plan records their implementation.
The duplicate QUALITY_AUDIT.md was removed; retain this record as historical evidence.
