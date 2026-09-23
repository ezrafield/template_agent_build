# Conventions

## Code
- Keep modules focused on one responsibility.
- Prefer explicit names over clever abbreviations.
- Add dependencies only when they solve a clear problem.
- Keep generated files separate from hand-written files.

## Tests
- Put fast isolated tests in `tests/unit/`.
- Put cross-boundary tests in `tests/integration/`.
- Use fixtures for reusable setup data.

## Documentation
- Keep the shared `AGENTS.md` concise.
- Put task-specific details in `.agent/tasks/`.
- Put durable system knowledge in `docs/agent/`.
- Put product intent in `docs/product/`.
