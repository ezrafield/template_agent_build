# Behavioral evaluation

Run `python eval/behavior/run_behavior_eval.py` (or `make behavior-eval`) to
validate six controlled tasks offline. Every initial state must fail and every
reference solution must pass independently held acceptance checks. No model,
network, or paid call is made by the default command.

The cases cover iterable bug fixing, feature edge cases, a behavior-preserving
refactor, source-grounded documentation, stale and duplicate memory, and following
linked context. Each `case.json` specifies an exact permitted project diff.
Acceptance checks and reference files live outside each trial workspace. The
grader snapshots files rather than trusting an agent's summary or git status.
These controlled fixtures are not an adversarial code-execution sandbox.

## Optional matched live experiment

```bash
python eval/behavior/run_behavior_eval.py --live --model YOUR_MODEL --baseline-ref ddc2831131c949780b2abc3d966c3f357359286e
python eval/behavior/run_behavior_eval.py --live --model YOUR_MODEL --baseline-ref BASELINE_COMMIT --case bug-fix --repeat 3 --timeout 300
```

Both model and baseline revision are mandatory for a live run. An authenticated
Codex CLI is required. The evaluator archives the exact baseline commit and
captures the current candidate harness, including uncommitted harness edits,
with a content digest. Each trial uses that arm's actual installer and a fresh
git repository. The behavior corpus is excluded from both installations to keep
reference answers and acceptance checks out of the writable repository. The
same fixture, prompt, model, sandbox, execution limits, and guardrail activation
procedure apply to both arms; order alternates to reduce order effects.

Trials use `workspace-write`, approval policy `never`, enabled hooks, and the
installed command rules. Existing host hook trust still applies: the evaluator
does not bypass it, disable hooks, or ignore rules. Confirm the host has approved
the installed hook definitions before interpreting live results as guardrail
coverage. No network, dependency installation, commits, or guardrail edits are
requested. Each trial defaults to 300 seconds and one repetition, with no retries;
the runner terminates the subprocess tree on timeout. New plan/task notes and
ignored context caches are allowed, while existing instructions remain protected.

Reports are written to ignored `.agent/traces/evals/behavior-*.json`. They contain
correctness, scope violations, failures, elapsed seconds, observed command count,
generated context-bundle character count, and available token usage. Bundle size
is a local artifact measurement, not total prompt size. Missing usage/cost is
`null`; raw agent events, command text, credentials and hidden reasoning are not
stored. CLI quality outcomes are informational; infrastructure failures return
nonzero and remain in the denominator.

Review matched outcomes, sample size, scope violations, and failures before
claiming gains. Do not claim improvement if candidate task success declines or
new scope violations appear. Effectiveness is **not yet measured** until matched
live trials have been completed and reviewed.
