# Task: Plan Evolution Governance

## Goal

Add a global plan-record rule and a core skill that supports learning from plans
and upgrades.

## User Request

Require every plan and upgrade to be saved as a file so the user and AI can
evaluate and improve their shared mindset and strategy.

## Relevant Docs Read

- `AGENTS.md` and `docs/agent/INDEX.md`
- Agent, skill, Codex customization, tool, MCP, and memory guidance routed by the index
- `skill-creator`, `safe-implementation`, and `memory-maintenance` instructions

## Files Inspected

- Existing skill catalog, manifest, validator, tests, routing corpus, plan
  template, memory cards, and Claude compatibility entrypoint

## Assumptions

- The existing `.agent/plans/` lifecycle is the canonical plan folder.
- Direct read-only answers and unplanned one-step actions are not plans.

## Plan

1. Record this upgrade before implementation.
2. Add the root rule and `plan-evolution` skill.
3. Upgrade the template, catalog, validator, routing fixtures, docs, and memory.
4. Run focused and broad agent-asset checks.

## Changes Made

- Added the global plan-evolution rule to Codex and Claude entrypoints.
- Added and registered the `plan-evolution` core skill.
- Expanded the plan template around hypothesis, evidence, and user/AI learning.
- Added deterministic plan-system validation, routing cases, installer coverage,
  documentation, and verified project memory.

## Commands Run

| Command | RTK Used | Raw Rerun | Reason |
| --- | --- | --- | --- |
| Targeted reads with `Get-Content` and `rg` | no | no | Route context and inspect integration points |
| `init_skill.py plan-evolution` | no | no | Create the required skill scaffold |
| `quick_validate.py .agents/skills/plan-evolution` | no | yes | Validate skill structure; rerun after replacing a Unicode quote |
| `pytest tests/agent/test_validate_agent_assets.py -q` | no | no | Exercise plan validation |
| `run_skill_routing_eval.py --validate-only` | no | no | Validate routing fixtures |
| `validate_memory_links.py` and `audit_memory_staleness.py` | no | no | Verify promoted memory |
| `validate_agent_assets.py` | no | no | Validate the integrated agent system |
| `pytest tests/agent -q` | no | yes | Broad regression; rerun after updating stale skill count |
| Installer, docs, compile, and diff checks | no | no | Verify packaging and static integrity |

## Token / Context Notes

- Reads were limited to routed agent, skill, validation, plan, and memory files.
- No repository-wide content scan or external lookup was needed.

## Verification

Skill validation passed; 18 routing cases cover 9 skills; 13 agent tests passed;
agent assets reported 0 errors and 0 warnings; installer, docs, memory, compile,
and whitespace checks passed. `make` was unavailable, so the underlying Python
validator was run directly.

## Memory Extraction

- Candidate generated: no
- Promotion needed: completed
- Notes: Updated the existing verified conventions card directly because the
  rule is already supported by root instructions, the core skill, and tests.

## Follow-Up

Evaluate several completed records before adding aggregate metrics or automation.
