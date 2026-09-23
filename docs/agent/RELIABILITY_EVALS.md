# Optional Reliability Experiments

Use these tools when studying the kit, not as prerequisites for ordinary coding.
Track task outcomes, elapsed time, commands, context size, and usage separately
from asset validity and skill selection. Live effectiveness is **not yet measured**.

## Offline Checks

```bash
make behavior-eval
make advice-eval
make skill-routing-eval
```

These Make shortcuts belong to the reference checkout. Installed kits can use
`python eval/behavior/run_behavior_eval.py`,
`python eval/advice/run_advice_eval.py`, and
`python eval/skills/run_skill_routing_eval.py`. These make no model, network, or
paid calls. The aggregate `python eval/run_eval.py` is reference-checkout-only.
Routine CI runs the bounded core pytest suite and lightweight asset/compilation
checks. The manual `agent-doc-check` workflow also validates these research
corpora and the pinned Codex runtime without paid calls. Detailed experiment
edge cases have intentionally reduced unit coverage.

The six behavioral cases cover a bug, edge-case feature, refactor, documentation,
conflicting memory, and missing context. Initial solutions must fail, references
must pass, and 14 reviewed incorrect mutations must fail within the permitted
diff. Graders use file snapshots and independently held checks; protected initial
sources are integrity-checked. Documented inline or fenced CLI examples are
parsed against the original parser without executing command text.
See [fixture maintenance](../../eval/behavior/README.md) for the file contract.
These controlled fixtures are not an adversarial sandbox or exhaustive proof of
grader correctness, natural-language claim validity, or live effectiveness.

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

Live runs require an authenticated Codex CLI and explicit model and baseline
revision. The initial v0.4 baseline is `ddc2831131c949780b2abc3d966c3f357359286e`.
The evaluator archives that exact revision and hashes the current candidate
harness, including uncommitted edits. Each arm uses its own installer in a fresh,
disposable Git repository; neither receives the behavior corpus or reference
answers. Fixtures, prompts, model, limits, and guardrail activation match across
arms, with alternating execution order.

Trials use `workspace-write`, approval policy `never`, disabled workspace network,
enabled hooks, and installed command rules. Host hook trust is retained: confirm
the installed definitions are approved before claiming guardrail coverage.
Authentication or unsupported runtimes must not weaken these controls. Trial
tasks prohibit network requests, package installation, commits, and guardrail
edits. New plan/task notes and ignored caches are allowed; existing instructions
and memories remain protected unless explicitly permitted by the fixture.

Use `--case ID` to select cases, `--repeat N` to repeat them (default 1), and
`--timeout SECONDS` to change the 300-second trial limit. There are no automatic
retries; timeout terminates the subprocess tree.

Reports in ignored `.agent/traces/evals/behavior-*.json` retain correctness,
failures, scope violations, elapsed time, command count, context size, and
available token usage. Unknown usage/cost stays `null`; measured tokens are not
billed cost. Raw events, prompts, command text, credentials, and hidden reasoning
are excluded. Quality outcomes are informational; infrastructure failures return
nonzero and remain in the denominator.
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

Follow [code-review](../../.agents/skills/code-review/SKILL.md) for independent
review and [task-handoff](../../.agents/skills/task-handoff/SKILL.md) for checkpoint
and resume requirements.
