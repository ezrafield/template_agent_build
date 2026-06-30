# RTK Integration

RTK is optional but recommended for token-efficient command execution.

## Purpose

RTK compresses noisy terminal output before an AI agent sees it. It is part of the context layer, not the correctness layer.

## Recommended Usage

- Local coding agents: enable an RTK hook when the agent runtime supports hooks.
- Codex-style agents: use `AGENTS.md` command-output rules and optional make wrappers.
- CI: do not require RTK for correctness.
- Debugging: allow raw output fallback for exact failures and generated artifacts.

## Verify

```bash
rtk --version
rtk gain
python scripts/run_agent_tool.py rtk --version
make rtk-gain
```

## Project-Local Bootstrap

RTK is pinned in `tools/agent/rtk-manifest.json`. Run:

```bash
make agent-tools-install
make agent-tools-check
```

The bootstrap downloads the matching release asset, verifies its SHA-256 checksum, and extracts `rtk` or `rtk.exe` into `tools/agent/bin/`. Generated binaries are ignored.

Use the project wrapper to prefer this binary without changing PATH:

```bash
python scripts/run_agent_tool.py rtk --version
python scripts/run_agent_tool.py --fallback git status -- rtk git status
```

## Disable For One Command

```bash
RTK_DISABLED=1 <command>
```

## Design Notes

- RTK should degrade gracefully. If it is missing or filtering fails, run the original command.
- Project make wrappers prefer workspace-local RTK and use raw fallback only when RTK is unavailable.
- Keep raw command access available for security review, artifact verification, and unclear failures.
- Record compressed-vs-raw command usage in task logs when a task needs an audit trail.
