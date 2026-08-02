# Codex Customization

This project separates durable instructions, reusable workflows, deterministic
lifecycle automation, command escalation policy, and evaluation.

## Instruction Discovery

Codex builds project instructions once per run. Starting at the repository root
and walking to the working directory, it selects at most one file per level in
this order:

1. `AGENTS.override.md`
2. `AGENTS.md`
3. configured fallback filenames

The selected files are concatenated root-to-leaf. A same-level override replaces
that level's normal file; it does not remove ancestor instructions. The default
combined project budget is 32 KiB and is configurable. This repository enforces
smaller internal budgets with `make validate-agent-assets`.

Use `AGENTS.override.md.example` for temporary root replacement. Keep intentional
nested overrides tracked; only the root local override is ignored.

## Skills

Codex discovers repository skills under `.agents/skills/`. Every skill must have
`name` and trigger-focused `description` frontmatter, concise instructions, and
matching UI metadata. The manifest records command dependencies and the unified
validator checks discovery, size, naming, and catalog coverage.

## Opt-In Hooks and Rules

Run:

```bash
make codex-guardrails-enable
make codex-runtime-check
```

The enable command generates machine-local `.codex/hooks.json` and
`.codex/rules/default.rules` from committed templates. It resolves absolute
handler paths, refuses overwrite, and adds local Git excludes when possible.
Restart Codex, open `/hooks`, review the exact definitions, and trust them before
expecting command hooks to run.

The initial hooks are:

- `SessionStart`: report missing required commands or core kit assets.
- `UserPromptSubmit`: block conservative secret patterns without logging or
  echoing the prompt.
- `Stop`: validate changed agent assets and use `stop_hook_active` to avoid a
  continuation loop.

`SessionEnd` metrics are intentionally deferred because end timing is advisory
and transcript-derived telemetry introduces privacy and reliability concerns.

Command rules apply to commands requesting execution outside the sandbox. The
template prompts for package installation, pushes, hard resets, migrations, and
deployment operations; exact catastrophic root-deletion commands are forbidden.
There are no `allow` rules. Rules supplement rather than replace sandboxing,
permissions, approvals, and hooks.

## Evaluation

- `make validate-agent-assets`: deterministic instruction, skill, manifest, and
  template checks.
- `make codex-runtime-check`: Codex feature and `execpolicy` fixtures; no API
  authentication required.
- `python eval/agent/run_hook_eval.py`: deterministic hook behavior fixtures.
- `make skill-routing-eval`: authenticated, non-gating routing measurements.

The routing corpus reports precision, recall, forbidden activations, and
collision rate. It remains observational until repeated runs establish a stable
baseline.

## Official References

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Hooks](https://learn.chatgpt.com/docs/hooks)
- [Rules](https://learn.chatgpt.com/docs/agent-configuration/rules)
