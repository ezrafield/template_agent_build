# ADR 0005: Measurable Reliability and Shadow Advice

Status: accepted
Date: 2026-09-22

## Context

The v0.4 kit validates assets and routing, but those checks cannot establish
whether its workflows improve completed tasks. Memory dates and file existence
also miss content drift. Optional semantic advice should be measurable before
it can influence deterministic behavior.

## Decision

- Add offline behavioral fixtures with evaluator-owned acceptance checks and
  reference solutions. Explicit live experiments compare the captured baseline
  and candidate in isolated workspaces under equal limits and safeguards.
- Keep reports separate from context bundles, in ignored `.agent/traces/evals/`.
  Do not persist credentials, raw prompts, or hidden reasoning. Missing usage and
  billed costs remain unknown; unsuccessful trials remain in accounting.
- Extend memory index version 1 with optional normalized-text source hashes.
  Legacy entries remain valid and untracked; new/reverified promotion requires
  evidence. Drift means re-verification, never automatic invalidation or promotion.
- Amend ADR 0004's selection order only for explicit expansion requests:
  required routed excerpts, caller-requested ranges, optional routed excerpts,
  then advisory search. Preserve budgets and default behavior, re-read sources,
  count each path once, and keep structured compiler state in memory.
- Use acceptance criteria and an independent review for multi-module behavior
  and public-contract changes. Bound the automatic review sequence to initial
  review plus one re-review; unresolved material findings remain visible.
- Add a typed provider-neutral advisory interface and a stdlib Jev adapter.
  Explicit live requests send only a redacted task and catalog descriptions.
  Advice has no execution authority, no hook integration, and no automatic retries.
- Ship deterministic validation in CI. Live effectiveness remains not yet
  measured until matched results are available; no paid model calls are required.

## Alternatives

Active model routing would add uncalibrated behavior to the baseline. A large
orchestration framework or memory database would change portability and ownership
without evidence of benefit. Pure asset validation cannot answer outcome questions.
The selected design adds optional measurements and local controls incrementally.

## Consequences

The agent-kit becomes v0.5.0 without changing the sample application's version,
memory index version, or installer ownership. Existing user memory is preserved.
New CLI flags and reports need validation and installation coverage. Synthetic
fixtures are small and do not establish general performance or production safety.
Any active routing successor needs its own plan and matched empirical evidence.

## Token Efficiency Follow-Up (2026-09-23)

A local routing audit found unrelated optional-source matches and substantial
metadata overhead. Tighten optional relevance and bound large optional excerpts;
required routes and explicit expansions retain priority. Add a compact Markdown
reading companion with a complete-output budget, while retaining the full audit
at the original cache path. This amends the earlier one-artifact presentation;
neither Markdown file becomes authoritative state and there is no JSON sidecar.
Compact memory lookup keeps fingerprints in the validator's input and returns
summaries with current evidence states. Reuse current task context across skills,
link existing plan/check evidence in checkpoints, and require explicit live flags
for skill-routing experiments. Measured reading-size reductions do not establish
improved task success or billed savings.

## Evidence

- [Jev primitives](https://docs.typesafe.ai/introduction)
- [Skill-induced failures, August 2026](https://arxiv.org/abs/2608.11888)
- [Memory evaluation, July 2026](https://www.letta.com/blog/evaluating-memory-in-production-agents/)
- [Recursive context research](https://arxiv.org/abs/2512.24601)
- [Selective independent evaluation](https://www.anthropic.com/engineering/harness-design-long-running-apps)
