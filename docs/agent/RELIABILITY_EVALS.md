# Reliability Evaluations

v0.5 measures task outcomes separately from asset validity and skill selection.
Correctness and scope come first; time, commands, context size, and usage are
secondary observations. Live effectiveness is **not yet measured** by offline tests.

## Offline Checks

```bash
make behavior-eval
make advice-eval
make skill-routing-eval
python eval/run_eval.py
```

Direct Python equivalents are `python eval/behavior/run_behavior_eval.py`,
`python eval/advice/run_advice_eval.py`, and
`python eval/skills/run_skill_routing_eval.py`. These require no model key or paid call.
CI validates fixtures and tests fake runners/transports. The six behavioral cases
cover a bug, edge-case feature, refactor, documentation, conflicting memory, and
missing context. Checks belong to the evaluator; an agent's success claim does
not determine the result. Reference solutions verify fixture feasibility.

## Optional Live Skill Routing

```bash
python eval/skills/run_skill_routing_eval.py --live --model MODEL --limit 3 --timeout 300
```

The default command and `make skill-routing-eval` validate all routing fixtures
offline, even when an authenticated Codex CLI is installed. `--validate-only`
remains an alias for this default and cannot be combined with `--live`.
Live measurements require both `--live` and an explicit non-empty `--model`;
neither `--model` nor `--limit` enables model calls by itself. `--limit` selects
the first N live cases; it never reduces offline fixture validation.

Routing trials ask which skills would activate without executing the quoted
task. Each case defaults to a 300-second timeout with no automatic retry.
Failed and timed-out cases remain explicit and count as recall misses.
Precision, recall, forbidden activations, and collision rate are informational;
skill selection alone does not demonstrate successful task completion.

## Matched Behavioral Trials

```bash
python eval/behavior/run_behavior_eval.py --live --model MODEL --baseline-ref REVISION
```

The initial v0.4 baseline is `ddc2831131c949780b2abc3d966c3f357359286e`.
Select a smaller smoke experiment with `--case ID`; use `--repeat N` for repeated
measurements. Each trial has a default 300-second timeout and no automatic retry.
The same fixtures, model, and runtime safeguards apply to baseline and candidate.
Trials use disposable workspaces, never the user's checkout. Authentication or
unsupported runtime configurations must not silently weaken execution controls.

Reports live in ignored `.agent/traces/evals/`. They retain failed-trial accounting,
scope violations, elapsed time, command count, context size, and available token
usage. Unknown metrics remain null, and measured tokens are not a billed cost.
Raw prompts, credentials, and hidden reasoning do not belong in reports.
`context_characters` estimates the available generated reading context: prefer
each compact `.read.md` companion and use its full `.md` audit only when no
compact companion exists, including v0.4 baseline bundles. It never counts both
views of one bundle. No readable bundle means unknown (`null`); this estimate
does not establish what the agent actually read or how many tokens it consumed.

Before claiming improved reliability, compare matched results with no new scope
violations and no lower task success. Report sample size, per-case regressions,
infrastructure failures, and uncertainty. These small synthetic fixtures are a
diagnostic tool, not proof of broad superiority. Live results do not gate ordinary CI.

## Jev Shadow Measurements

```bash
python eval/advice/run_advice_eval.py --live --model jev-1.13.0
```

Set `TYPESAFE_API_KEY` in the environment; never place it in a command argument,
tracked file, or report. Omit `--live` for offline fixture validation. `--case ID`
selects labels covering paraphrases, mixed intents, ambiguity, and unrelated tasks.
The versioned model is pinned; an explicit `--model` can change the experiment.

The adapter sends the redacted task and route/skill descriptions only. It asks
for a route (including insufficient-information and out-of-scope options), each
skill's relevance, and clarification need. It never sends repository contents or
conversation history. Requests time out after ten seconds without retries.
Missing credentials or invalid/unavailable responses become explicit unavailable
results. Reports include the returned model, probabilities, latency, and usage.

Accuracy includes unavailable attempts in its overall denominator. Brier scores
measure probability error on available labeled samples. Skill and clarification
accuracy use a 0.5 reporting threshold only; this is not an execution threshold.
Vendor confidence describes the probability distribution and is not a guarantee
of correctness. Advice cannot change routes, expansions, permissions, or tests.

## Review and Handoff

For multi-module behavior changes or public-contract changes, agree on observable
acceptance criteria and give an independent reviewer the request, diff, and
verification evidence. Use a separate agent/session where possible, and disclose
same-context review. Allow an initial review and one re-review after fixes.
Unresolved material findings block a completion claim. Simple documentation and
low-impact edits retain normal verification.

Use the task-log checkpoint to preserve completed criteria, open findings,
verified revision and dirty state, checks, external effects, and next action.
On resume, verify current state and rerun only checks affected by relevant edits.
