---
name: test-scope
description: Choose the smallest sufficient test set when adding, reviewing, or pruning tests, or when a suite exceeds its budget. Use for test scope and maintenance decisions; do not use for running an unchanged focused check.
---

# Test Scope

Minimize test maintenance and execution cost while retaining evidence for the
behavior that matters. Test count is a constraint, not a quality score.

1. Read project testing instructions and the relevant implementation. Identify
   observable acceptance criteria, consequential failure modes, and any explicit
   suite budget. Respect project and user requirements; do not impose a universal cap.
2. Inspect existing coverage before adding anything. For each proposed test,
   name the distinct regression it would catch and why existing checks miss it.
   Prefer extending an existing relevant assertion over a new overlapping case.
3. Keep representative public behavior, risky boundaries, known consequential
   regressions, and permission/data/ownership protections. Remove duplicate paths,
   framework or dataclass trivia, implementation-mirroring assertions, and obsolete
   behavior. Choose one useful test layer rather than repeating the same contract.
4. Count actual collected cases, including parameterized rows and skips. For
   pytest use `python -m pytest --collect-only -q`; use the framework's equivalent
   elsewhere. Never meet a cap by hiding cases in loops, deselecting files, moving
   the old suite out of discovery, or weakening assertions just to pass.
5. For a full budget, replace lower-value coverage before adding a case. If the
   required behaviors cannot fit safely, explain the concrete conflict and obtain
   a scope/budget decision instead of silently dropping essential coverage.
6. Pure prose, mechanical, or reversible low-impact edits often need only an
   existing check or direct inspection. Add a test only when it protects a
   meaningful behavior. Keep experimental matrices opt-in when project policy allows.
7. Run focused checks, then the required suite once. Repeat only after a relevant
   change or failure. Report before/after counts, checks run, and any coverage
   deliberately removed. State what the evidence proves; fewer cases alone do
   not establish faster execution or improved reliability.

Keep the rationale in the existing plan, review, or final response. Do not create
another test inventory document or new test framework for a small cleanup.
