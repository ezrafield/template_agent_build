# MCP Setup

This directory documents candidate Model Context Protocol servers for the project.

Do not commit secrets here.

## Candidate MCPs

| Name | Purpose | Scope |
| --- | --- | --- |
| Semble | Natural-language code and repo search | Default retrieval profile |
| Serena | Language-server backed symbols, references, diagnostics, and refactors | Optional advanced coding profile |
| filesystem | Structured local project access | Read/write by project root |
| github | Issues, PRs, CI, review threads | Repository metadata and selected actions |
| browser | Local UI verification | Browser automation |
| docs | Current official documentation | Read-only |
| database | Schema and safe queries | Prefer read-only |
| RTK | Optional compressed terminal output for agent sessions | Agent runtime integration, not CI correctness |

## Configuration Notes

- Keep project-specific MCP config separate from user-local secrets.
- Prefer read-only permissions until write access is required.
- Record required setup steps in `docs/agent/COMMANDS.md`.
- Use `servers.example.json` as a placeholder, not as a working secret-bearing config.
- Run `make agent-tools-install` or `python scripts/bootstrap_agent_tools.py` to recreate project-local optional tools.
- Keep Semble as the default project search profile.
- Keep Serena optional; enable it only for projects that benefit from language-server semantics.
- Keep RTK optional; fall back to raw commands whenever it is unavailable or compressed output is unclear.
- Keep generated tool binaries, virtual environments, and caches ignored.
