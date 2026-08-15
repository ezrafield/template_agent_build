QUERY ?=
CONTENT ?= code
PATTERN ?=
LANG ?= python
REPOMIX_ARGS ?= .
ROUTE ?=
TASK_CONTEXT_ROUTE_ARG = $(if $(ROUTE),--route "$(ROUTE)",)

.PHONY: install agent-tools-install agent-tools-check agent-kit-check dev test test-unit test-integration lint typecheck docs-map agent-setup validate-docs validate-agent-docs validate-agent-assets codex-guardrails-enable codex-runtime-check skill-routing-eval task-context task-context-explain task-context-eval detect-large-context-docs detect-large-agent-files check-context-staleness audit-module-cards audit-task-logs validate-memory-links audit-memory-staleness audit-memory check-architecture-boundaries update-module-cards targeted-tests task-trace extract-task-memory code-search repomix ast-grep rtk-gain git-status git-diff test-unit-compact lint-compact typecheck-compact understand understand-dashboard understand-search validate-understand-graph retrieval-eval

install: agent-tools-install
	@echo "Install project dependencies here."

agent-tools-install:
	python scripts/bootstrap_agent_tools.py

agent-tools-check:
	python scripts/bootstrap_agent_tools.py --check

agent-kit-check:
	python scripts/agentkit_installer.py check --source . --target .

dev:
	@echo "Start the development server here."

test: test-unit test-integration

test-unit:
	python -m pytest tests/unit tests/agent -q

test-integration:
	python -m pytest tests/integration -q

lint:
	python -m compileall -q src scripts eval tests
	python scripts/validate_agent_assets.py

typecheck:
	@echo "Run type checks here."

docs-map:
	python scripts/generate_codemap.py

agent-setup:
	python scripts/agent_setup.py

validate-docs:
	python scripts/validate_docs.py

validate-agent-docs:
	python scripts/validate_agent_docs.py

validate-agent-assets:
	python scripts/validate_agent_assets.py

codex-guardrails-enable:
	python scripts/enable_codex_guardrails.py

codex-runtime-check:
	python scripts/check_codex_runtime.py

skill-routing-eval:
	python eval/skills/run_skill_routing_eval.py

task-context:
	python scripts/task_context.py build "$(TASK)" $(TASK_CONTEXT_ROUTE_ARG)

task-context-explain:
	python scripts/task_context.py explain "$(TASK)" $(TASK_CONTEXT_ROUTE_ARG)

task-context-eval:
	python eval/context/run_task_context_eval.py

detect-large-context-docs:
	python scripts/detect_large_context_docs.py

detect-large-agent-files:
	python scripts/detect_large_agent_files.py

check-context-staleness:
	python scripts/check_context_staleness.py

audit-module-cards:
	python scripts/audit_module_cards.py

audit-task-logs:
	python scripts/audit_task_logs.py

validate-memory-links:
	python scripts/validate_memory_links.py

audit-memory-staleness:
	python scripts/audit_memory_staleness.py

audit-memory: validate-memory-links audit-memory-staleness

check-architecture-boundaries:
	python scripts/check_architecture_boundaries.py

update-module-cards:
	python scripts/update_module_cards.py

targeted-tests:
	python scripts/run_targeted_tests.py

task-trace:
	python scripts/collect_task_trace.py

extract-task-memory:
	python scripts/extract_task_memory.py $(TASK)

code-search:
	python scripts/run_agent_tool.py semble search "$(QUERY)" . --content "$(CONTENT)"

repomix:
	python scripts/run_agent_tool.py repomix $(REPOMIX_ARGS)

ast-grep:
	python scripts/run_agent_tool.py ast-grep run --pattern "$(PATTERN)" --lang "$(LANG)" .

rtk-gain:
	@python scripts/run_agent_tool.py rtk gain || echo "rtk not installed or not initialized"

git-status:
	python scripts/run_agent_tool.py --fallback git status -- rtk git status

git-diff:
	python scripts/run_agent_tool.py --fallback git diff -- rtk git diff

test-unit-compact:
	python scripts/run_agent_tool.py --fallback make test-unit -- rtk test make test-unit

lint-compact:
	python scripts/run_agent_tool.py --fallback make lint -- rtk proxy make lint

typecheck-compact:
	python scripts/run_agent_tool.py --fallback make typecheck -- rtk proxy make typecheck

understand:
	python scripts/understand_placeholder.py

understand-dashboard:
	@echo "Open the Understand Anything dashboard with the installed runtime command, for example /understand-dashboard."

understand-search:
	python scripts/search_understand_graph.py "$(QUERY)"

validate-understand-graph:
	python scripts/validate_understand_graph.py

retrieval-eval:
	python eval/retrieval/run_retrieval_eval.py
