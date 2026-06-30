# Serena MCP Profile

Serena is an optional advanced coding profile. Do not require every project or contributor to install it.

## When To Enable

Enable Serena for serious coding projects where language-server semantics matter, especially:
- Python
- TypeScript
- Java
- C#
- Go

## Best Uses

- Find declarations and implementations.
- Find all symbol references.
- Inspect diagnostics.
- Navigate class, function, and method relationships.
- Plan safe multi-file refactors and renames.

## Agent Policy

Use Serena after CODEMAP/module cards, Semble, and `rg` when exact symbol relationships or diagnostics affect correctness.

Do not use Serena as the first step for every task. The default template profile remains Semble + `rg` + CODEMAP/module cards.

## Setup Notes

Serena is pinned in `tools/agent/python/serena/pyproject.toml` and `tools/agent/python/serena/uv.lock` as `serena-agent==1.5.3`. Do not install the unrelated PyPI package named `serena`.

```bash
make agent-tools-install
python scripts/run_agent_tool.py serena --help
```

Serena has its own `uv` environment because its dependency pins conflict with Semble's runtime search dependency needs.

Document project-specific Serena startup, language-server requirements, and workspace roots here after adoption. Keep secrets and user-local paths out of this file.
