# Workflows

## Add A Feature
1. Build and review a task-context bundle for the feature.
2. Read the relevant module card and verify selected excerpts.
3. Inspect one similar implementation.
4. Add the smallest complete implementation.
5. Add or update focused tests.
6. Run targeted checks.
7. Update docs when behavior changes.

## Fix A Bug
1. Reproduce the bug with a failing test or command.
2. Build and review a `bug-fix` task-context bundle.
3. Read the module card for the affected area.
4. Patch the narrowest responsible code.
5. Add a regression test.
6. Run targeted tests.

## Refactor
1. Identify the behavior that must remain unchanged.
2. Build and review a `refactor` task-context bundle.
3. Read architecture and relevant module cards.
4. Prefer small mechanical steps.
5. Keep tests passing between steps when possible.
6. Avoid changing public contracts unless explicitly requested.

## Review Or Decide

1. Build a `code-review` or `architecture-decision` bundle.
2. Confirm warnings and provenance before relying on selected excerpts.
3. Expand only where exact references, full files, or dependency graphs matter.
4. Keep reviews read-only; record consequential architecture choices in an ADR.
