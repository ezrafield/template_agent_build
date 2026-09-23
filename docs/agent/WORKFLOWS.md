# Workflows

Reuse already-inspected context for the same task and route. Rebuild when the
task, route, requested ranges, or relevant sources change; never assume an old
cache is current. Read compact output first and open the full audit only when
selection or provenance needs inspection. A new skill does not require rereading
unchanged context. Query memory with `python scripts/memory_lookup.py "<task>"`.
Link shared plan and verification records in task checkpoints rather than copying them.
Optimize for completed acceptance criteria and low total effort. Use `test-scope`
when changing coverage; keep docs to the smallest useful surface. Research
evaluations are opt-in and are not prerequisites for everyday implementation.

## Add A Feature
1. State observable acceptance criteria, then reuse or build a current task-context bundle for the feature.
2. Read the relevant module card and verify selected excerpts.
3. Inspect one similar implementation.
4. Add the smallest complete implementation.
5. Reuse coverage; add a focused test only for an uncovered meaningful behavior.
6. Run targeted checks.
7. Update docs when behavior changes.
8. For multi-module behavior or public-contract changes, obtain independent review
   using the existing `code-review` skill and record evidence in the task checkpoint.

## Fix A Bug
1. Reproduce the bug with a failing test or command.
2. Reuse or build a current `bug-fix` task-context bundle.
3. Read the module card for the affected area.
4. Patch the narrowest responsible code.
5. Retain a regression test when existing coverage misses a consequential failure.
6. Run targeted tests.

## Refactor
1. Identify the behavior that must remain unchanged.
2. Reuse or build a current `refactor` task-context bundle.
3. Read architecture and relevant module cards.
4. Prefer small mechanical steps.
5. Keep tests passing between steps when possible.
6. Avoid changing public contracts unless explicitly requested.

## Review Or Decide

1. Reuse or build a current `code-review` or `architecture-decision` bundle.
2. Confirm warnings and provenance before relying on selected excerpts.
3. Expand only where exact references, full files, or dependency graphs matter.
4. Keep reviews read-only; record consequential architecture choices in an ADR.
5. Review the request and acceptance criteria against actual artifacts and checks.
   Disclose review independence; unresolved material findings block completion.
   Allow an initial review and one re-review after fixes.
