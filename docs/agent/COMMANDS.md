# Commands

Detected project commands.

- dev: `make dev`
- agent-tools-check: `make agent-tools-check`
- agent-tools-install: `make agent-tools-install`
- agent-kit-check: `make agent-kit-check`
- ast-grep: `make ast-grep`
- code-search: `make code-search`
- git-diff: `make git-diff`
- git-status: `make git-status`
- lint: `make lint`
- lint-compact: `make lint-compact`
- codex-guardrails-enable: `make codex-guardrails-enable`
- codex-runtime-check: `make codex-runtime-check`
- repomix: `make repomix`
- rtk-gain: `make rtk-gain`
- test: `make test`
- test-integration: `make test-integration`
- test-unit: `make test-unit`
- test-unit-compact: `make test-unit-compact`
- typecheck: `make typecheck`
- typecheck-compact: `make typecheck-compact`
- validate-agent-assets: `make validate-agent-assets`
- understand: `make understand`
- understand-dashboard: `make understand-dashboard`
- understand-search: `make understand-search`

Agent tool bootstrap:
- agent-tools-install: `make agent-tools-install`
- agent-tools-check: `make agent-tools-check`
- no-make install: `python scripts/bootstrap_agent_tools.py`
- no-make check: `python scripts/bootstrap_agent_tools.py --check`

Source understanding helpers:
- code-search: `make code-search QUERY="source understanding" CONTENT=all`
- ast-grep: `make ast-grep PATTERN="def $NAME($$$ARGS): $$$BODY" LANG=python`
- repomix: `make repomix`

Optional compact-output helpers:
- rtk-gain: `make rtk-gain`
- git-status: `make git-status`
- git-diff: `make git-diff`
- test-unit-compact: `make test-unit-compact`
- lint-compact: `make lint-compact`
- typecheck-compact: `make typecheck-compact`

Memory helpers:
- extract-task-memory: `make extract-task-memory TASK=.agent/tasks/<task>.md`
- validate-memory-links: `make validate-memory-links`
- audit-memory-staleness: `make audit-memory-staleness`
- audit-memory: `make audit-memory`

Codex customization:
- validate all static assets: `make validate-agent-assets`
- verify the installed kit: `make agent-kit-check`
- generate local guardrails: `make codex-guardrails-enable`
- validate Codex rules: `make codex-runtime-check`
- run authenticated routing metrics: `make skill-routing-eval`
