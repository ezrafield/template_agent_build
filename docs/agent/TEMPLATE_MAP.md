# Template Map

Architecture, routing, workflow, and coordination in kit **0.5.0**, checked
2026-09-23. Open this file in a Markdown viewer with Mermaid support to see the
drawings. Follow the source links for implementation details.

**The coding assistant coordinates the task.** The template supplies instructions,
context selection, skills, and checks. It has no always-running orchestration
service. A context route selects reading material; it does not select a model,
launch an agent, or execute a skill.

Quick reading: **request → assistant → focused context → work → checks → daily
summary → response**. Independent review is added when the change requires it.

## 1. Architecture: what talks to what?

```mermaid
flowchart LR
    User["User request"] --> Agent["Coding assistant<br/>Task coordinator"]
    Policy["AGENTS.md<br/>Shared project instructions"] --> Agent
    Skills["Skills<br/>Reusable workflow instructions"] --> Agent
    Agent -->|"build context"| Compiler["task_context.py<br/>Deterministic Python compiler"]
    Routes["context-routes.json<br/>Selection rules"] --> Compiler
    Repo["Current code, tests and docs"] --> Compiler
    Compiler -->|"Markdown context + diagnostics"| Agent
    Agent <-->|"query and verify"| Memory["Project memory<br/>Cards + source evidence"]
    Agent -->|"inspect and edit"| Repo
    Agent -->|"run"| Checks["Focused tests<br/>Applicable validation"]
    Agent -->|"record"| Records["Daily change log<br/>Plan or handoff when needed"]
```

The host, such as Codex or a supported Claude Code session, supplies the model,
tools, permissions, and any subagent capability. The kit supplies the project
workflow. Shared instructions do not imply identical skill discovery across hosts;
see [host compatibility](AGENTS_AND_SKILLS.md#claude-code-compatibility).

| Part | Where to inspect it |
| --- | --- |
| Shared instructions and completion rules | [AGENTS.md](../../AGENTS.md) |
| Routes and context compiler | [route manifest](context-routes.json), [compiler](../../scripts/task_context_engine.py) |
| Available workflows | [skills catalog](AGENTS_AND_SKILLS.md) |
| Memory lookup and evidence | [memory guide](MEMORY_RETRIEVAL.md) |
| Sample application's API/service/model layers | [application architecture](ARCHITECTURE.md) |

## 2. Routing: how is context chosen?

```mermaid
flowchart TD
    Task["Task text"] --> Override{"Explicit --route?"}
    Override -->|"yes"| Exact["Use the named route<br/>Unknown ID is an error"]
    Override -->|"no"| Intent{"Any workflow intent rules match?"}
    Intent -->|"yes"| IntentSet["Consider matching routes"]
    Intent -->|"no"| All["Consider all routes"]
    IntentSet --> Score["Score matching trigger phrases<br/>Break ties by manifest order"]
    All --> Score
    Score --> Choice["Select one route<br/>No intent or trigger match: general"]
    Exact --> Required["1. Required routed excerpts"]
    Choice --> Required
    Required --> Expansion["2. Explicit line ranges, if requested"]
    Expansion --> Optional["3. Relevant optional routed excerpts"]
    Optional --> Search["4. Advisory Semble results, if enabled"]
    Search --> Bundle["Compact .read.md + full audit .md<br/>Inspect warnings, gaps and omissions"]
```

Multiple matching intents or tied best scores produce an ambiguity warning.
The compiler still chooses deterministically; the assistant inspects that choice
and can rerun with `--route`. Trigger matching is literal phrase logic, not a
model's understanding of arbitrary intent.

Every source passes containment, exclusion, secret-file, redaction, and budget
checks. Selection allows **10 distinct files and 40,000 excerpt characters**;
the compact reading view also caps its complete rendered output at 40,000
characters. Lower-priority content cannot displace required excerpts. Required
means priority, not guaranteed completeness: even required excerpts can be
missing or visibly truncated. If selected required/explicit reading content and diagnostics cannot fit,
compact rendering fails instead of silently dropping them.

The 13 routes include `bug-fix`, `api-endpoint`, `database-change`,
`frontend-change`, `refactor`, `planning-product`, `agent-system`,
`memory-maintenance`, `agent-setup`, `source-understanding`, `code-review`,
`architecture-decision`, and `general`.

Try the actual router from the project root:

```bash
python scripts/task_context.py explain "Review the API diff" --no-search
python scripts/task_context.py build "Fix the API regression" --route bug-fix --no-search
```

Builds read current sources; cached Markdown is never authoritative input.
Reuse an inspected bundle only while its task/options and relevant sources stay
current. For a missing fact, request `--expand-source PATH START END --reason
"why needed"`, supplying all desired ranges each time. Expansion is deliberate;
there is no automatic retrieval loop. Details: [context guide](CONTEXT_ROUTER.md).

## 3. Workflow: how does a change get finished?

A typical non-trivial change follows this path:

```mermaid
flowchart TD
    Request["Understand request and observable acceptance criteria"] --> Plan["Record a plan when required"]
    Plan --> Context["Reuse or build context<br/>Inspect warnings; verify useful memory"]
    Context --> Work["Inspect current source<br/>Make the smallest complete change"]
    Work --> Verify["Run focused checks<br/>Broader checks proportional to risk"]
    Verify --> Pass{"Checks pass?"}
    Pass -->|"no"| Fix["Reproduce and correct<br/>or report a blocker"]
    Fix -->|"corrected"| Verify
    Pass -->|"yes"| NeedReview{"Multiple modules' behavior<br/>or public contract changed?"}
    NeedReview -->|"no"| Finish["Update necessary docs and reviewed memory<br/>Close plan when applicable"]
    NeedReview -->|"yes"| Review["Independent review<br/>Fix findings; at most one re-review"]
    Review --> Resolved{"Material findings resolved?"}
    Resolved -->|"yes"| Finish
    Resolved -->|"no"| Blocked["Preserve findings<br/>Report incomplete work"]
    Fix -->|"blocked"| Blocked
    Finish --> Log["After edits: append today's change log<br/>Preserve earlier entries"]
    Blocked --> Log
    Log --> Reply["Report result or blocker<br/>Checks and remaining risks"]
```

These arrows describe the assistant's workflow, not a Python state machine.
`safe-implementation`, `test-debug-loop`, `test-scope`, and `code-review` provide
instructions as relevant. The reference suite is capped at **49 collected cases**;
adopted projects choose their own budget. Read-only tasks need no daily entry.
Plans live in `.agent/plans/`; pause/resume checkpoints live in `.agent/tasks/`;
daily summaries live in `change_logs/YYYY-MM-DD.md` using the local date.

## 4. Coordination: who calls whom?

Example: a task changes an API contract and service behavior, so it needs review.

```mermaid
sequenceDiagram
    actor User
    participant Agent as Coding assistant
    participant Context as Context compiler
    participant Repo as Repository and checks
    participant Reviewer as Independent reviewer
    User->>Agent: Change the API contract and service behavior
    Agent->>Context: Build focused context
    Context-->>Agent: Selected sources, warnings and gaps
    Agent->>Repo: Verify sources, implement, run checks
    Agent->>Reviewer: Request, criteria, diff and check evidence
    Reviewer-->>Agent: Findings with evidence and impact
    opt Material findings
        Agent->>Repo: Fix findings and run affected checks
        Agent->>Reviewer: One re-review
        Reviewer-->>Agent: Remaining findings or clear review
    end
    Agent->>Repo: Update daily log and applicable plan or handoff
    Agent-->>User: Verified result or unresolved blocker
```

Use a separate agent/session for review when available; disclose review in the
same context otherwise. The host assistant starts and coordinates it. Skills are
instructions, not independent background workers.

Optional components have limited roles:

| Component | Role |
| --- | --- |
| Semble | Advisory source suggestions after routed and explicit context. |
| Serena / RTK | Symbol navigation / command-output compression when useful. |
| Opt-in hooks and rules | Lifecycle checks and command guardrails, not task scheduling. |
| Jev | Explicit shadow experiment: records advice; cannot choose execution routes, permissions, expansion, or completion. |
| Research evaluations | Explicit local runs or manual CI; live model runs require explicit flags. |

Routine CI runs the core tests, Python compilation, and asset validation.
Memory promotion stays manual. Optional experiments are described in the
[evaluation guide](RELIABILITY_EVALS.md); live effectiveness remains unmeasured.
