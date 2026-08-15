# Plan: Agent Kit v0.4 Task Context Compiler

## Metadata

- Created: 2026-08-15
- Updated: 2026-08-15
- Kind: upgrade
- Status: completed
- Owners: user and AI
- Version / Relation: agent-kit 0.4.0; follows `.agent/plans/completed/2026-08-07-plan-evolution-governance.md`

## Goal

Upgrade the agent kit from instruction-guided context loading to an explicit,
inspectable Markdown task-context bundle while preserving deterministic routes,
optional tooling, safe local reads, and dependency-free operation.

## Why This Strategy

Treating task context as a disposable build artifact should make selection,
omissions, provenance, and budget visible without replacing the existing
progressive context router. Golden fixtures make the new behavior testable,
while route-first selection keeps optional semantic search advisory.

## Scope

In scope: v0.4 versioning; route manifest; Markdown bundle builder and explain
command; optional Semble adapter; safe reads and redaction; golden evaluation;
task-context skill and workflow integration; installer, validation, docs, ADR,
and memory updates.

Out of scope: a contextd dependency, JSON artifact sidecars, multi-workspace
knowledge, context packs, policy-as-code, prompt logging, and automatic hooks.

## Success Signals

- Routed documents always precede advisory search results.
- Bundles contain warnings, selection trace, hashes, budget data, and excerpts.
- Unsafe or missing sources produce warnings without blocking a valid bundle.
- Golden fixtures cover every route and pass without Semble installed.
- Agent assets, installer checks, tests, lint, and existing evaluations pass.

## Execution Outline

- [x] Record the durable architecture decision.
- [x] Implement the route manifest, context engine, CLI, and Markdown renderer.
- [x] Add deterministic golden fixtures and focused unit/integration coverage.
- [x] Add the task-context skill and integrate non-trivial workflows.
- [x] Bump and synchronize v0.4 installer, validation, docs, and memory surfaces.
- [x] Run focused and broad verification and capture outcome evidence.

## Decisions And Changes

- 2026-08-15 — Persist Markdown bundles only; keep the structured build model in memory for evaluation.
- 2026-08-15 — Use a validated JSON route manifest; `INDEX.md` remains the human-facing route catalog.
- 2026-08-15 — Required routes are authoritative; Semble may append within a 10-document, 40,000-character budget.
- 2026-08-15 — Materialize one ignored, atomically replaced bundle per normalized task hash.
- 2026-08-15 — Treat context gaps as warnings; reserve exit code 2 for invalid input/configuration or failed materialization.

## Risks And Assumptions

- Markdown output must remain stable enough for humans without becoming a second machine-readable schema.
- Search output may vary, so deterministic golden evaluation disables or stubs Semble.
- Route and INDEX drift must be caught by agent-asset validation.
- Secret-pattern redaction is conservative and does not replace repository access controls.

## Verification

- Focused task-context unit and CLI tests.
- Deterministic golden route evaluation.
- Full unit and integration tests, lint, and agent-asset validation.
- Agent-kit installer check and existing skill/retrieval/runtime evaluations.

## Outcome And Evidence

Completed the v0.4 upgrade with a Python-stdlib engine, thin CLI, validated
13-route manifest, tenth skill, Markdown-only cache artifact, optional Semble
adapter, installer/setup integration, and synchronized agent documentation.

- `python -m pytest -q`: 33 passed, 2 environment-specific skips.
- Focused task-context/installer/asset tests: 25 passed, 2 skips.
- `python eval/context/run_task_context_eval.py`: 13/13 routes passed.
- Authenticated skill routing: 20 cases covering all 10 skills passed with
  precision 1.000, recall 1.000, collision rate 0.000, and no forbidden activations.
- Agent-asset validation: 0 errors and 0 warnings.
- Installed-project setup and golden evaluation passed in the installer test.
- Compile, docs, module-card, context-staleness, memory-link, and memory-staleness checks passed.
- Hook evaluation passed 4 cases; Codex runtime evaluation passed 9 rule cases.
- A live compiler `explain` run successfully consumed project-local Semble JSON
  and re-read selected local ranges.

The skipped tests were Windows symlink creation and a Make integration test on
a machine without `make`; CI installs Make on Ubuntu and runs `tests/agent` plus
the golden evaluator.

## Reflection

- What worked: A route-first in-memory model kept policy, rendering, CLI behavior,
  and golden evaluation testable without adding a persisted JSON schema.
- What did not: The first installed-project smoke test exposed that the manifest
  was not copied and setup assumed `src/` existed; focused reproduction led to
  owning the manifest and making source-map refresh conditional.
- User mindset/strategy learning: Preserve the template's lightweight workflow
  while borrowing the inspectability and provenance ideas, not the full upstream system.
- AI workflow/prompt/context learning: Installed-project tests catch ownership
  and portability failures that source-tree validation cannot reveal.
- Next experiment: Observe real task classifications and dropped-source traces
  before considering reusable packs, policy layers, or prompt integration.

## Follow-Up

Create a linked successor rather than expanding v0.4 into packs, policy, or
automatic hooks.
