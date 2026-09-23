# Behavioral Fixtures

See [Reliability Evaluations](../../docs/agent/RELIABILITY_EVALS.md) for commands,
live-run safeguards, reporting, and interpretation.

Each directory under `fixtures/` contains:

- `case.json`: task request and exact permitted project-file changes.
- `initial/` and `reference/`: starting state and a feasible correct solution.
- `acceptance.py`: evaluator-owned checks, outside the trial workspace.
- `mutations.json`: reviewed edits representing plausible incorrect solutions.

Mutation edits must target permitted files, match old text exactly once, and
change that text. Each runs against a fresh reference workspace. Stale recipes,
accepted mutations, integrity changes, scope violations, and timeouts fail validation.
