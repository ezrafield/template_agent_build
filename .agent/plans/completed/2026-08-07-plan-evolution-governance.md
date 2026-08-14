# Plan: Plan Evolution Governance

## Metadata

- Created: 2026-08-07
- Updated: 2026-08-07
- Kind: upgrade
- Status: completed
- Owners: user and AI
- Version / Relation: agent-kit 0.3.0 behavior update; no release bump

## Goal

Make every plan and upgrade in this agent-native template leave a durable,
reviewable record so the user and AI can evaluate and improve their shared
mindset and strategy over time.

## Why This Strategy

The working hypothesis is that recording intent before execution and comparing
it with evidence afterward will reveal which assumptions, decisions, and AI
collaboration patterns are effective. The record must stay lightweight enough
to be used consistently.

## Scope

- Add a root instruction that requires plan and upgrade records.
- Add a core repository skill for the record lifecycle.
- Upgrade the shared plan template to capture hypotheses, evidence, and learning.
- Register and document the skill in the agent kit.
- Add focused routing and validation coverage where the current harness expects it.

Out of scope: automated analytics across historical records and external
telemetry.

## Success Signals

- A future agent can identify when a record is mandatory from root instructions.
- The core skill explains create, maintain, close, and review behavior.
- The template separates predicted value from observed evidence and learning.
- The agent-asset validator and focused tests pass.

## Execution Outline

- [x] Record this upgrade before implementation.
- [x] Add the global instruction and core skill.
- [x] Upgrade template, catalog, manifest, docs, validation, routing, and memory.
- [x] Run focused checks before broader agent-kit validation.
- [x] Close this record with evidence and learning.

## Decisions And Changes

- 2026-08-07 — Reused the existing `.agent/plans/` lifecycle instead of
  introducing a competing top-level folder.
- 2026-08-07 — Made `plan-evolution` a required, implicitly invokable core skill
  and mirrored the rule in `CLAUDE.md` for cross-agent coverage.
- 2026-08-07 — Added deterministic checks for lifecycle directories, record
  naming, required learning headings, and instruction markers.
- 2026-08-07 — Deferred aggregate scoring until several real records exist.

## Risks And Assumptions

- Risk: mandatory records become bureaucracy for trivial actions.
- Mitigation: require them for actual plans and upgrades, not read-only answers
  or tiny actions that do not create a plan.
- Assumption: `.agent/plans/` is the canonical "plan folder" because it already
  ships with lifecycle subdirectories in the template.

## Verification

- `quick_validate.py`: skill valid.
- `pytest tests/agent/test_validate_agent_assets.py -q`: 5 passed.
- Routing fixture validation: 18 cases and 9 skills valid.
- Memory link validation: 6 promoted cards valid.
- `pytest tests/agent -q`: 13 passed.
- `validate_agent_assets.py`: 0 errors and 0 warnings; 1 plan record validated.
- Installer check: agent kit 0.3.0 structurally valid; optional `make` unavailable.
- Memory staleness, docs validation, Python compile, and diff whitespace checks passed.

## Outcome And Evidence

All success signals were met. `AGENTS.md` remains below the internal 4 KiB
target at 4008 bytes. The installed catalog now contains 9 required skills, and
fresh-install coverage confirms the new skill is packaged. The first broad test
run exposed one stale eight-skill assertion; updating it made all 13 agent tests
pass.

## Reflection

- What worked: starting from an actual active record forced the new lifecycle to
  prove itself during implementation, and the existing plan directories kept
  the change small.
- What did not: the first skill validation failed on a Unicode quote under the
  Windows code page, and the first broad test exposed a hard-coded skill count.
  Both failures are retained here because they improved portability and coverage.
- User mindset/strategy learning: a useful plan is an experiment with explicit
  success signals and reflection, not just a checklist of tasks.
- AI workflow/prompt/context learning: a global rule becomes dependable only
  when discovery, packaging, validation, routing, compatibility docs, and memory
  all reinforce the same behavior.
- Next experiment: after 3-5 completed records, compare which hypotheses and
  collaboration patterns repeatedly predict successful outcomes.

## Follow-Up

Keep the format lightweight during real use. If it becomes burdensome, revise
the template through a new linked upgrade record rather than silently skipping
it. Rollback remains possible by removing the skill and manifest/catalog
entries, reverting the root rule and template, and retaining this record as
evaluation evidence.
