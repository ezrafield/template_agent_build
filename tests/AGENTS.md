# tests/AGENTS.md

## Testing Conventions
- Put isolated tests in `tests/unit/`.
- Put boundary or cross-module tests in `tests/integration/`.
- Keep fixtures in `tests/fixtures/`.
- Prefer targeted tests before broad suites.
- This template permits at most 49 collected pytest cases, including parameterized rows and skips; `tests/conftest.py` enforces the cap. Adopted projects should set their own budget.
- Use `test-scope` when adding or pruning tests. Protect core behavior and meaningful regressions; remove overlap before growing the suite. Never disguise independent cases in loops or excluded files.
- Optional research corpora under `eval/` are manual experiments, outside the core suite and routine CI.
