# Commands

Detected project commands.

- agent-kit-check: `make agent-kit-check`
- agent-tools-check: `make agent-tools-check`
- agent-tools-install: `make agent-tools-install`
- ast-grep: `make ast-grep`
- code-search: `make code-search`
- codex-guardrails-enable: `make codex-guardrails-enable`
- codex-runtime-check: `make codex-runtime-check`
- dev: `make dev`
- git-diff: `make git-diff`
- git-status: `make git-status`
- lint: `make lint`
- lint-compact: `make lint-compact`
- repomix: `make repomix`
- retrieval-eval: `make retrieval-eval`
- rtk-gain: `make rtk-gain`
- skill-routing-eval: `make skill-routing-eval`
- task-context: `make task-context`
- task-context-eval: `make task-context-eval`
- task-context-explain: `make task-context-explain`
- test: `make test`
- test-integration: `make test-integration`
- test-unit: `make test-unit`
- test-unit-compact: `make test-unit-compact`
- typecheck: `make typecheck`
- typecheck-compact: `make typecheck-compact`
- understand: `make understand`
- understand-dashboard: `make understand-dashboard`
- understand-search: `make understand-search`
- validate-agent-assets: `make validate-agent-assets`

Agent tool bootstrap:
- agent-tools-install: `make agent-tools-install`
- agent-tools-check: `make agent-tools-check`
- no-make install: `python scripts/bootstrap_agent_tools.py`
- no-make check: `python scripts/bootstrap_agent_tools.py --check`

Source understanding helpers:
- code-search: `make code-search QUERY="source understanding" CONTENT=all`
- ast-grep: `make ast-grep PATTERN="def $NAME($$$ARGS): $$$BODY" LANG=python`
- repomix: `make repomix`

Task context compiler:
- build: `make task-context TASK="describe the task"`
- explain: `make task-context-explain TASK="describe the task"`
- evaluate: `make task-context-eval`

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
- validate-agent-assets: `make validate-agent-assets`
- agent-kit-check: `make agent-kit-check`
- codex-guardrails-enable: `make codex-guardrails-enable`
- codex-runtime-check: `make codex-runtime-check`
- skill-routing-eval: `make skill-routing-eval`
