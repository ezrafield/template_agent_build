# Memory: Testing Playbooks

Type: procedural
Scope: testing
Confidence: medium
Last verified: 2026-09-23
Source task: .agent/tasks/README.md
Verification record: .agent/memory/verification/2026-09-23-token-efficiency.md

## When to use

Use this memory when choosing verification commands for behavior changes.

## Procedure

1. Start with the smallest test that covers the changed behavior.
2. Reuse existing coverage. Use `test-scope` when adding or pruning tests; this template allows at most 49 collected cases, including parameterized rows and skips. Other projects choose their own budget.
3. Run applicable lint and static analysis when code, interfaces, or generated context changes. The bundled `typecheck` target is a placeholder; wire a real project check before counting it as validation.
4. Use compact Make targets when output may be noisy.
5. Record commands, failures, raw reruns, and skipped checks in the final response or task log.
6. Keep research evaluations optional. Passing fixtures or reducing the suite does not establish improved agent effectiveness.

## Verification commands

```bash
make test-unit
make lint
make typecheck
```

## Related files

- `Makefile`
- `scripts/run_targeted_tests.py`
- `docs/agent/COMMAND_OUTPUT_POLICY.md`
- `.agents/skills/safe-implementation/SKILL.md`
- `.agents/skills/test-scope/SKILL.md`
- `docs/agent/RELIABILITY_EVALS.md`

## Staleness triggers

- Make targets change.
- Test framework changes.
- Lint or typecheck commands change.
