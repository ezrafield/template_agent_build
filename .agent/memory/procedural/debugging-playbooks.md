# Memory: Debugging Playbooks

Type: procedural
Scope: debugging
Confidence: medium
Last verified: 2026-09-23
Source task: .agent/tasks/README.md
Verification record: .agent/memory/verification/2026-09-23-token-efficiency.md

## When to use

Use this memory when a test, script, command, or runtime path is failing.

## Procedure

1. Reproduce the failure with the smallest command that shows it.
2. Reuse an inspected current bug-fix bundle or build one for non-trivial failures; refresh changed context and read the relevant module card or `docs/agent/CODEMAP.md`.
3. Use compressed output when available; rerun the narrow raw command if details are unclear.
4. Inspect the responsible source and adjacent tests only after retrieval identifies likely targets.
5. Patch the smallest responsible area.
6. Re-run the targeted failure, then broader checks when risk justifies it.

## Verification commands

```bash
make targeted-tests
make test-unit
```

## Related files

- `docs/agent/INDEX.md`
- `docs/agent/COMMAND_OUTPUT_POLICY.md`
- `.agents/skills/test-debug-loop/SKILL.md`
- `Makefile`

## Staleness triggers

- Test command wiring changes.
- RTK or command output policy changes.
- Debugging skill guidance changes.
