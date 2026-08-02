---
name: test-debug-loop
description: Reproduce, isolate, fix, and re-test a failing test or runtime error. Use when a command, CI check, or application path is failing; do not start with broad suites when a focused reproduction exists.
---

# Test Debug Loop

1. Run the smallest failing test or deterministic reproduction.
2. Preserve the complete actionable error and identify the first relevant failure.
3. Form one root-cause hypothesis and verify it against current code.
4. Apply the smallest correction that addresses that cause.
5. Re-run the exact reproduction before expanding test scope.
6. Run adjacent regression checks after the focused check passes.
7. Report the failing command, cause, patch, verification, and any remaining uncertainty.

Keep each loop focused on one failure. Do not hide stack traces or replace root-cause analysis with repeated broad retries.
