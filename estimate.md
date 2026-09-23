# Estimated Benefits With Progressive Context, Memory, And RTK

This estimate models how much time, token usage, and rework this template can save when it combines three context controls:

1. Progressive source retrieval:
   `AGENTS.md` -> `docs/agent/INDEX.md` -> module cards / `CODEMAP.md` -> Semble -> `rg` -> optional Serena -> targeted files.
2. Lightweight long-term memory:
   inspect `.agent/memory/index.json` -> load only relevant semantic or procedural cards -> verify them against current files before use.
3. RTK-aware command output:
   compact `git`, search, test, lint, typecheck, and log output by default, with raw reruns only when exact details matter.

These are directional estimates, not benchmark guarantees. Use `make retrieval-eval`, `make rtk-gain`, task traces, and provider usage logs to measure your own project.

## What Changed With Long-Term Memory Joining

The new memory layer targets repeated orientation work that source retrieval and
output compression do not preserve across tasks. It separates semantic facts
and conventions, procedural playbooks, and episodic task logs. Only compact,
reviewed lessons are promoted; current code, tests, and docs remain the source
of truth.

| Memory stage | Template control | Expected effect |
| --- | --- | --- |
| Capture | Structured `.agent/tasks/` logs | Retains task evidence without auto-loading it |
| Extraction | `make extract-task-memory` | Converts verbose task history into a reviewable candidate |
| Promotion | Manual review plus `.agent/memory/index.json` | Keeps reusable knowledge discoverable and limits low-quality memory |
| Retrieval | Scope and keyword lookup after `INDEX.md` | Reduces repeated searches for known conventions and workflows |
| Verification | Related files, source task, confidence, and staleness triggers | Prevents memory from silently overriding current repository state |
| Audit | Link validation and a 180-day staleness check | Surfaces missing evidence and aging cards |

This is intentionally a lightweight, PlugMem-inspired design rather than a
PlugMem dependency. It adds no embedding service, graph database, model server,
or API-key requirement.

## What Changed With RTK Joining

Before RTK, this template mostly reduced tokens spent reading the wrong files. RTK adds a second savings layer: reducing tokens spent reading noisy terminal output.

| Context source | Template control | Memory control | RTK control | Expected effect |
| --- | --- | --- | --- | --- |
| Broad source reads | Index, module cards, CODEMAP, Semble, `rg` | Recalled file and workflow hints | None | Fewer irrelevant files loaded |
| Git status / diff | Compact make targets | None | RTK filters | Shorter patch review loops |
| Search output | Targeted `rg` / Semble | Fewer repeated discovery searches | `rtk grep`, `rtk find` | Less repeated scan noise |
| Test output | Targeted tests first | Recalled test-selection playbooks | `rtk pytest`, `rtk npm test`, `rtk cargo test` | Failures stay visible without full logs |
| Lint / typecheck output | Compact make targets | None | `rtk eslint`, `rtk tsc` | Faster diagnosis of actionable errors |
| Large runtime logs | Manual narrowing | Recalled debugging procedures | RTK log filtering when available | Lower context-window pressure |

RTK is part of the context layer, not the correctness layer. It should preserve failures, degrade gracefully when missing, and allow raw output reruns whenever compressed output is incomplete or suspicious.

## Assumptions

| Factor | Small repo | Medium repo | Large repo |
| --- | ---: | ---: | ---: |
| Source files | 50-150 | 150-800 | 800-3,000 |
| Average file size | 150-300 lines | 150-350 lines | 150-400 lines |
| Typical task scope | 1-3 modules | 2-5 modules | 3-8 modules |
| Baseline source behavior | Reads many likely files | Reads module trees | Reads broad folders or repo bundles |
| Baseline command behavior | Raw command output | Raw noisy test/diff output | Raw logs, broad diffs, large suites |
| Template behavior | Reads routed context and likely targets; compresses noisy command output when RTK is available |

## Token Savings

### Source Context

| Scenario | Baseline source context | Template source context | Estimated savings |
| --- | ---: | ---: | ---: |
| Small bug fix | 25k-60k tokens | 8k-20k tokens | 40%-70% |
| Medium feature change | 80k-180k tokens | 20k-55k tokens | 60%-80% |
| Cross-module refactor | 150k-400k tokens | 45k-120k tokens | 55%-75% |
| Onboarding / architecture question | 100k-300k tokens | 25k-90k tokens | 50%-75% |
| External whole-repo review | 250k+ tokens | No major savings if a full Repomix export is required | 0%-20% |

Expected average across normal coding tasks: **50%-75% fewer source-context input tokens**.

### Incremental Memory Impact

Memory overlaps with progressive retrieval, so its benefit should not be added
directly to the source-context savings above. The clearest gains occur when a
repository has recurring task types and reviewed memory cards that still match
the current codebase.

| Scenario | Expected incremental effect beyond routed retrieval |
| --- | ---: |
| First task in a new area or no relevant memory | 0%-5% fewer routine input tokens |
| Repeated task with a relevant verified card | 5%-20% fewer routine input tokens |
| Recurring debugging or test-selection workflow | 10%-30% fewer discovery and diagnosis loops |
| Stale, broad, or low-quality memory | No expected gain; may increase rework |

Across a mixed workload, a conservative planning assumption is **0%-10%
additional routine input-token savings** beyond progressive retrieval and RTK,
with larger task-level gains only when relevant memory is reused. Treat this as
a hypothesis until task traces compare work with and without memory retrieval.

### Command Output

RTK savings vary more by workflow than source savings. A task with one clean unit test may save very little. A task with repeated test failures, large diffs, or broad lint output can save a lot.

| Command/output type | Raw output pattern | With RTK or compact wrappers | Estimated savings |
| --- | ---: | ---: | ---: |
| `git status` / `git diff` | Full status and patch context | Condensed file/change summary | 30%-70% |
| Search output | Many matches and paths | Ranked or reduced matches | 30%-75% |
| Passing tests | Full runner output | Short pass summary | 40%-80% |
| Failing tests | Full trace/log output | Actionable failure sections preserved | 20%-60% |
| Lint/typecheck | Long issue lists | Compact actionable diagnostics | 30%-70% |
| Runtime logs | Large raw log blocks | Filtered relevant sections | 40%-85% |

Expected average across command-heavy coding tasks: **25%-60% fewer command-output tokens**.

### Combined Context Impact

For a typical implementation task, assume:

- 70%-85% of input context is source/docs.
- 15%-30% of input context is command output.
- Progressive retrieval saves 50%-75% of source/docs context.
- RTK saves 25%-60% of command-output context when available.

That yields a practical combined estimate of **45%-75% fewer routine input tokens** across normal agent-assisted coding tasks.

For a team doing 100 agent-assisted coding tasks per month, with a baseline of 100k input tokens per task:

| Savings rate | Monthly input context after template | Tokens saved/month |
| --- | ---: | ---: |
| 45% | 5.5M tokens | 4.5M tokens |
| 60% | 4.0M tokens | 6.0M tokens |
| 75% | 2.5M tokens | 7.5M tokens |

## Time Savings

| Activity | Baseline | With template + RTK | Estimated savings |
| --- | ---: | ---: | ---: |
| Initial repo orientation per task | 5-20 min | 1-5 min | 50%-80% |
| Finding relevant files | 5-30 min | 2-8 min | 40%-75% |
| Inspecting git diff/status | 2-10 min | 1-4 min | 30%-60% |
| Confirming related tests | 3-15 min | 1-5 min | 40%-70% |
| Diagnosing test/lint/typecheck output | 5-30 min | 2-12 min | 30%-65% |
| Reviewing agent context choices | 5-15 min | 2-6 min | 40%-60% |
| New contributor/agent onboarding | 2-8 hr | 30-90 min | 50%-85% |

Expected average for normal implementation tasks: **10-50 minutes saved per task**, depending on repo size, command noise, and ambiguity.

For 100 tasks per month, that is roughly **17-83 engineering hours saved per month**.

## Cost Savings Model

Use this formula:

```txt
monthly_token_savings =
  tasks_per_month
  * baseline_input_tokens_per_task
  * combined_savings_rate
```

Example:

```txt
100 tasks/month * 100,000 input tokens/task * 0.60 savings
= 6,000,000 input tokens saved/month
```

If input tokens cost `C` dollars per million tokens:

```txt
monthly_cost_savings = 6 * C
```

This excludes secondary savings from fewer retries, fewer wrong-file edits, shorter review cycles, reduced output tokens, and less human time spent reading noisy command output.

## Other Quantitative Benefits

| Benefit | Estimated impact |
| --- | ---: |
| Fewer irrelevant files read by agents | 50%-80% reduction |
| Less noisy command output in context | 25%-60% reduction on command-heavy tasks |
| Faster first useful patch | 30%-70% faster |
| Fewer wrong-file edits | 20%-50% reduction |
| Fewer "where is this implemented?" loops | 40%-70% reduction |
| Faster test selection | 30%-60% faster |
| Faster failure triage | 25%-60% faster |
| Lower context-window pressure | 45%-75% less routine context load |
| Better handoff quality | 25%-50% fewer missing-context handoffs |
| Lower chance of stale generated context being trusted blindly | Improved by explicit risk notes and validation checks |

## Why The Savings Happen

- `INDEX.md` routes the task to the smallest relevant context.
- `CODEMAP.md` gives a quick generated map of files, symbols, APIs, dependencies, tests, and risk notes.
- Module cards preserve ownership and pitfalls without reading full architecture docs.
- Reviewed memory cards recall durable facts and successful workflows without loading raw task logs.
- The JSON memory index supports small scope and keyword lookups before broader search.
- Manual promotion, source links, confidence, and staleness audits limit memory pollution.
- Semble finds behavior-level matches without knowing exact symbol names.
- `rg` confirms exact strings and paths cheaply.
- Serena is optional, so projects only pay the setup cost when language-server semantics are valuable.
- RTK compresses noisy terminal output while preserving actionable failures.
- Compact make targets keep command-output behavior discoverable for agents.
- Raw reruns remain available for exact failures, security review, and generated artifact verification.
- Repomix is kept out of the daily workflow, avoiding large bundled context by default.

## Measurement Plan

Track these metrics for 20-50 real tasks before and after installing the template:

| Metric | How to collect |
| --- | --- |
| Files read before first edit | Agent transcript or task trace |
| Input tokens per task | Model/provider usage logs |
| Command-output tokens per task | Agent transcript or RTK gain report |
| Time from task start to first patch | Task timestamps |
| Time from task start to accepted patch | Task timestamps |
| Search commands used | Agent transcript |
| Test commands used | Task handoff / logs |
| RTK used vs raw reruns | Command summary or task log |
| Wrong-file or reverted edits | Review notes |
| Missing-context review comments | PR comments |
| Relevant memory cards retrieved | Task trace or agent transcript |
| Memory hits verified or rejected | Task log memory-extraction notes |
| Time/tokens with and without memory | Paired recurring-task samples |
| Stale or broken memory cards | `make audit-memory` output |

Run retrieval checks with:

```bash
make retrieval-eval
```

Check RTK savings with:

```bash
make rtk-gain
```

Use the results to tune `docs/agent/CODEMAP.md`, module cards, `.sembleignore`, retrieval fixtures, compact make targets, and RTK command-output rules.

Audit the memory layer with:

```bash
make audit-memory
```

Review memory candidates and promoted cards separately; candidate count is not
a success metric. Useful reuse with successful verification is.

## Conservative Summary

For day-to-day agent-assisted coding, this template should reasonably save:

- **45%-75% routine input tokens overall**
- **0%-10% additional routine input tokens from verified memory reuse**
- **50%-75% source/docs input tokens**
- **25%-60% command-output tokens on command-heavy tasks**
- **10-50 minutes per normal coding task**
- **17-83 engineering hours per 100 tasks**
- **30%-70% faster file discovery**
- **20%-50% fewer wrong-context edits**

The largest gains come from medium and large repositories where agents otherwise read broad folders, bundled repo maps, raw diffs, full test output, and unrelated logs before editing.
