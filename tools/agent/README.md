# Agent Tool Workspace

This directory contains pinned manifests for optional agent tools that should be reproducible from a fresh checkout.

## Commit

- `python/semble/pyproject.toml` and `python/semble/uv.lock` for Semble.
- `python/serena/pyproject.toml` and `python/serena/uv.lock` for Serena.
- `package.json` and `package-lock.json` for Node tools: Repomix and ast-grep.
- `rtk-manifest.json` for the pinned RTK release assets and checksums.
- This README and the bootstrap scripts under `scripts/`.

## Do Not Commit

- `.venv/`
- `python/*/.venv/`
- `node_modules/`
- `bin/`
- `.uv-cache/`
- `.npm-cache/`
- `.hf-cache/`
- `.downloads/`

## Usage

```bash
make agent-tools-install
make agent-tools-check
```

If `make` is not available on Windows, use:

```bash
python scripts/bootstrap_agent_tools.py
python scripts/bootstrap_agent_tools.py --check
```

Prerequisites:

- Python
- `uv`
- Node.js 22+
- `npm`

Run tools through the project wrapper so global PATH setup is not required:

```bash
python scripts/run_agent_tool.py semble search "source understanding" . --content all
python scripts/run_agent_tool.py rtk git status
python scripts/run_agent_tool.py repomix --version
python scripts/run_agent_tool.py ast-grep --version
```

If this workspace is copied to another machine, rerun `make agent-tools-install` when the OS, CPU architecture, Python, Node, or absolute path changes.

The Python tool environments are intentionally created with Python 3.13 so Serena avoids Python 3.14 compatibility warnings from its transitive dependencies. Semble and Serena use separate uv environments because Serena pins `pathspec==0.12.1`, while Semble search needs a newer `pathspec` API.

The wrapper keeps Semble indexes under `.agent/context-cache/semble` and Hugging Face model files under `tools/agent/.hf-cache`; both are ignored.
