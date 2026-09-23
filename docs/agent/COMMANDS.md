# Commands

Detected project commands; verify placeholder targets before relying on them.

- advice-eval: `make advice-eval`
- agent-kit-check: `make agent-kit-check`
- agent-tools-check: `make agent-tools-check`
- agent-tools-install: `make agent-tools-install`
- ast-grep: `make ast-grep`
- behavior-eval: `make behavior-eval`
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

## Core Commands Without Make

- Validate assets: `python scripts/validate_agent_assets.py`
- Build context: `python scripts/task_context.py build "describe the task"`
- Look up memory: `python scripts/memory_lookup.py "task"`

Read the compact `.read.md`; reuse inspected context while the task, options,
ranges, and relevant sources remain current. Full audits and expansion are
documented in [Context Router](CONTEXT_ROUTER.md).

## Optional Tools and Detailed Usage

- Tool install: `python scripts/bootstrap_agent_tools.py`; check: add `--check`.
- [Tools and search](TOOLS.md); [tool workspace prerequisites](../../tools/agent/README.md).
- [Optional research evaluations and explicit live flags](RELIABILITY_EVALS.md).
- [Memory promotion and audits](MEMORY_PROMOTION_RULES.md).
- [Hooks, rules, and runtime checks](CODEX_CUSTOMIZATION.md).
