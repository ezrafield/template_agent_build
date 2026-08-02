# AI Template Improvement Plan

**File:** `02082026_improve_plan.md`
**Date:** 02 August 2026
**Project:** `ezrafield/template_agent_build`
**Purpose:** Improve the template based on OpenAI workshop concepts around project instructions, skills, rules, hooks, precedence, activation, installation, and evaluation.

---

## 1. Executive Recommendation

The template should clearly separate five concerns:

```text
AGENTS.md  → stable project instructions
Skills     → task-specific capabilities
Hooks      → deterministic lifecycle automation
Rules      → command permission and security policy
Evals      → verification that instructions, skills, hooks, and rules work
```

The most important immediate change is not to add more instructions. It is to:

1. reduce the size of the root `AGENTS.md`;
2. move specialized workflows into installable skills;
3. treat skills as versioned dependencies;
4. add byte-budget, activation, rule, and hook evaluations;
5. document precedence and activation behavior explicitly.

The target outcome is an agent-native project template that is:

- concise;
- predictable;
- installable;
- testable;
- secure;
- portable across projects;
- easier for Codex and similar coding agents to use reliably.

---

## 2. Problems in the Current Template

The current root `AGENTS.md` contains useful guidance, but it is beginning to combine too many responsibilities:

- project purpose;
- default workflow;
- context routing;
- memory rules;
- Semble usage;
- Serena usage;
- RTK usage;
- command catalog;
- code conventions;
- Definition of Done;
- response expectations.

This creates several risks:

1. Important instructions receive less attention.
2. The file becomes harder to maintain.
3. Specialized behavior is always loaded even when irrelevant.
4. New tools increase instruction length continuously.
5. Rule precedence becomes unclear.
6. Skills may be copied into the repository but not properly installed or discoverable.
7. Hooks may exist as files without being configured, trusted, or activated.
8. There is no systematic evaluation of instruction compliance or skill routing.

---

## 3. Target Architecture

```text
User Request
    ↓
System / Managed / User Policy
    ↓
Root AGENTS.md
    ↓
Nested AGENTS.md where relevant
    ↓
Skill selection
    ↓
Tool execution
    ↓
Hooks and command rules
    ↓
Tests and evaluations
    ↓
Task summary and audit
```

### Responsibility model

| Component | Responsibility |
|---|---|
| `AGENTS.md` | Stable project behavior and non-negotiable rules |
| Nested `AGENTS.md` | Directory-specific instructions |
| `AGENTS.override.md` | Temporary replacement of instructions at one directory level |
| Skills | Specialized task workflows |
| Tools | External capabilities such as Semble, Serena, RTK, GitHub, or MCP servers |
| Hooks | Deterministic automation around lifecycle events |
| Rules | Command execution permissions and security policy |
| Evals | Verification of routing, activation, precedence, and behavior |

---

## 4. Root `AGENTS.md` Redesign

### 4.1 Keep only stable instructions

The root file should contain:

1. Project purpose
2. Instruction hierarchy
3. Default workflow
4. Context-loading principles
5. Non-negotiable safety and code rules
6. Response style
7. Definition of Done
8. Links to `docs/agent/INDEX.md` and relevant skills

### 4.2 Move specialized content elsewhere

| Current content | New location |
|---|---|
| Semble commands and semantic search workflow | `semantic-code-search` skill |
| Serena navigation and refactoring workflow | `symbol-navigation` skill or tool guide |
| RTK command list | `command-output` skill or reference |
| Memory promotion workflow | `memory-maintenance` skill |
| Full command catalog | `docs/agent/TOOLS.md` |
| Detailed context discovery process | `repo-navigator` skill |
| Installation instructions | installers and dependency manifests |
| Tool-specific fallback rules | corresponding skill or tool reference |

### 4.3 Proposed root structure

```md
# AGENTS.md

## Project Purpose

## Instruction Hierarchy

## Default Workflow

## Context Rules

## Safety and Code Rules

## Response Style

## Definition of Done

## References
```

---

## 5. `AGENTS.override.md`

### 5.1 Intended use

`AGENTS.override.md` should be used for temporary or local replacement of normal instructions at a directory level.

Typical uses:

- temporarily prohibit migration changes;
- restrict the agent to targeted tests;
- require a plan before modifying sensitive modules;
- locally adjust behavior without editing shared project instructions.

### 5.2 Important behavior

At the same directory level:

```text
AGENTS.override.md replaces AGENTS.md
```

It should not be treated as an additive extension.

### 5.3 Template changes

Add:

```text
AGENTS.override.md.example
```

Add to `.gitignore`:

```gitignore
AGENTS.override.md
```

Use nested `AGENTS.md` for additive subdirectory specialization.

Use nested `AGENTS.override.md` only when intentionally replacing instructions for that directory.

### 5.4 Example

```md
# AGENTS.override.md

- Do not modify database migrations during this task.
- Run only targeted tests.
- Present a patch plan before editing authentication code.
```

---

## 6. `AGENTS.md` Byte Budget

### 6.1 Internal budget policy

The platform ceiling should not be treated as the target.

Recommended internal standards:

| Scope | Target | Warning threshold |
|---|---:|---:|
| Root `AGENTS.md` | ≤ 8 KiB | 10 KiB |
| Nested `AGENTS.md` | ≤ 4 KiB | 6 KiB |
| Combined root-to-directory chain | ≤ 16 KiB | 20 KiB |
| Platform default ceiling | 32 KiB | Hard limit |

### 6.2 Why byte budgets matter

Long instruction chains cause:

- higher prompt cost;
- reduced attention to important rules;
- more contradictions;
- harder maintenance;
- more accidental precedence conflicts;
- reduced prompt-cache stability;
- greater chance that later instructions are truncated.

### 6.3 New script

Add:

```text
scripts/check_agents_budget.py
```

Responsibilities:

1. Find all `AGENTS.md` and `AGENTS.override.md` files.
2. Calculate UTF-8 byte size.
3. Simulate root-to-leaf instruction chains.
4. Detect directories containing both normal and override files.
5. Warn about duplicated headings.
6. Detect likely repeated or conflicting instructions.
7. Fail CI when internal limits are exceeded.

### 6.4 New commands

```bash
make check-agent-budget
make validate-agent-instructions
```

---

## 7. Response Style

`## Response Style` should be treated as a clear project convention, not as a special parser keyword.

Recommended content:

```md
## Response Style

- Lead with the decision, result, or current status.
- For code changes, report:
  - files changed;
  - checks run;
  - remaining risks.
- Prefer concrete paths, commands, and diffs over long explanations.
- Keep progress updates brief unless a blocker requires detail.
- State assumptions and uncertainty explicitly.
```

Avoid vague instructions such as:

- “Be extremely intelligent.”
- “Think deeply.”
- “Act like a world-class engineer.”
- “Always be comprehensive.”

Response-style rules should describe observable behavior that can be evaluated.

---

## 8. Treat Skills Like Dependencies

### 8.1 Core principle

A skill is not merely a Markdown file.

A complete skill has:

- a name;
- a version;
- a source;
- an installation scope;
- supported agents or runtimes;
- activation criteria;
- tool dependencies;
- input and output expectations;
- tests;
- update and removal procedures.

### 8.2 Installation requirement

A skill is considered installed only when:

1. it is placed in a recognized skill directory;
2. its metadata is valid;
3. required commands or MCP servers are available;
4. its activation behavior is testable;
5. its dependencies are recorded;
6. the runtime can discover it.

Copying a skill into an arbitrary documentation folder is not installation.

### 8.3 Skill manifest

Add:

```text
agent-skills.lock.json
```

Example:

```json
{
  "schema_version": 1,
  "skills": [
    {
      "name": "repo-navigator",
      "source": "repo:.agents/skills/repo-navigator",
      "scope": "project",
      "required": true,
      "version": "1.0.0",
      "hosts": ["codex"],
      "dependencies": {
        "commands": ["rg"],
        "mcp_servers": []
      }
    },
    {
      "name": "semantic-code-search",
      "source": "repo:.agents/skills/semantic-code-search",
      "scope": "project",
      "required": false,
      "version": "1.0.0",
      "hosts": ["codex"],
      "dependencies": {
        "commands": ["semble"],
        "mcp_servers": []
      }
    }
  ]
}
```

### 8.4 Skill management scripts

Add:

```text
scripts/install_agent_skills.py
scripts/check_agent_skills.py
scripts/update_agent_skills.py
```

Add:

```bash
make skills-install
make skills-check
make skills-eval
```

### 8.5 Dependency separation

Distinguish clearly:

```text
Skill dependency
Tool dependency
MCP dependency
Runtime dependency
Project dependency
```

For example:

```text
semantic-code-search skill
    requires:
        semble command
        optional Semble MCP server
```

---

## 9. Shorter and Fewer Skills

### 9.1 Recommended initial skill set

Keep only approximately five to eight primary skills:

1. `repo-navigator`
2. `implement-change`
3. `debug-test-failure`
4. `review-change`
5. `task-audit`
6. `memory-maintenance`
7. optional `semantic-code-search`
8. optional `source-understanding`

### 9.2 Avoid skill fragmentation

Do not create a separate skill for:

- every shell command;
- every framework;
- every documentation file;
- every tool;
- every small workflow variation.

### 9.3 One skill, one job

Bad:

```text
general-engineering-assistant
```

Better:

```text
debug-test-failure
```

### 9.4 Internal size policy

| Skill artifact | Target |
|---|---:|
| Description | ≤ 300 characters |
| Main `SKILL.md` | ≤ 4 KiB |
| Primary steps | 5–10 |
| Primary responsibility | Exactly one |

### 9.5 Skill structure

```text
.agents/skills/debug-test-failure/
├── SKILL.md
├── references/
│   ├── python.md
│   └── typescript.md
├── scripts/
│   └── extract_failure.py
└── agents/
    └── openai.yaml
```

The main `SKILL.md` should remain concise.

Move these to `references/`:

- long examples;
- framework-specific notes;
- schemas;
- edge cases;
- detailed command documentation.

---

## 10. Skill Activation

### 10.1 Activation modes

Skills may activate:

1. explicitly, when named or selected;
2. implicitly, when the request matches the skill description.

The skill description therefore acts as a routing classifier.

### 10.2 Activation evaluation

Add:

```text
eval/skills/
├── activation_cases.json
├── expected_dependencies.json
└── run_skill_eval.py
```

Example:

```json
{
  "skill": "debug-test-failure",
  "should_activate": [
    "Fix this failing pytest",
    "CI fails with this stack trace",
    "Find the regression causing this test failure"
  ],
  "should_not_activate": [
    "Design a new authentication architecture",
    "Write a README",
    "Review this product idea"
  ]
}
```

### 10.3 Metrics

Track:

- activation precision;
- activation recall;
- false-positive activation rate;
- false-negative activation rate;
- multiple-skill collision rate;
- missing dependency rate;
- successful task completion after activation.

---

## 11. Rule Precedence

There is no single universal precedence model for all agent mechanisms.

### 11.1 Instruction precedence

```text
System
→ Developer or managed policy
→ User
→ Project instructions
→ Nested project instructions
→ Activated task-specific skills
```

Lower-level project instructions cannot override:

- system policy;
- managed organization policy;
- safety restrictions;
- explicit current-user constraints.

### 11.2 Project file precedence

```text
Global instructions
→ repository root
→ nested directories toward current working directory
```

Instructions nearer the working directory apply later and are more specific.

At the same directory level:

```text
AGENTS.override.md is preferred over AGENTS.md
```

### 11.3 Command rule precedence

When multiple command rules match:

```text
forbidden > prompt > allow
```

The most restrictive matching rule wins.

### 11.4 Hooks

Hooks do not use replacement precedence in the same way.

Multiple matching hooks may run.

A project hook does not automatically replace a higher-level hook.

### 11.5 New documentation

Add:

```text
docs/agent/INSTRUCTION_HIERARCHY.md
```

It should include:

- instruction role precedence;
- project file loading order;
- override behavior;
- skill activation behavior;
- rule resolution;
- hook activation;
- managed-policy constraints;
- examples of conflicts and expected outcomes.

---

## 12. Command Rules

### 12.1 Purpose

Rules should control command execution and security-sensitive actions.

Add:

```text
.codex/rules/default.rules
```

### 12.2 Suitable rule categories

Use rules for:

- safe test commands;
- lint and typecheck commands;
- package installation;
- network access;
- database migration;
- deployment;
- filesystem deletion;
- force pushes;
- secret inspection;
- privilege escalation.

### 12.3 Do not use rules for

- formatting preferences;
- naming conventions;
- documentation style;
- test coverage expectations;
- architecture advice.

Those belong in:

- `AGENTS.md`;
- skills;
- linters;
- tests;
- CI.

### 12.4 Initial policy

```text
Allow:
- make test-unit
- make lint
- make typecheck
- read-only git commands

Prompt:
- package installation
- network access
- database migration
- deployment
- changes to generated files
- changes to public APIs

Forbid:
- destructive recursive deletion
- force push to protected branches
- printing or exporting secrets
- disabling security checks without approval
```

### 12.5 Rule evaluations

Every rule should include or be paired with:

- expected matches;
- expected non-matches;
- expected resolution;
- precedence collision tests.

Add:

```text
eval/rules/
├── command_cases.json
└── run_rule_eval.py
```

---

## 13. Hooks

### 13.1 Core lesson

Hooks do not activate merely because hook scripts exist.

Activation requires:

1. hook configuration;
2. valid event mapping;
3. required runtime or executable;
4. trusted project or approved configuration;
5. smoke testing;
6. audit visibility.

### 13.2 Suggested configuration

```text
.codex/hooks.json
```

### 13.3 Initial hook set

Start with very few hooks:

| Event | Purpose |
|---|---|
| `SessionStart` | Check required tools and skills and report actionable missing dependencies |
| `UserPromptSubmit` | Detect obvious accidental secret exposure |
| `Stop` | Validate changed agent configuration files |
| `SessionEnd` | Record compact task metrics without raw sensitive content |

### 13.4 Avoid early overuse

Do not add hooks for every tool call initially.

Too many hooks cause:

- latency;
- noisy logs;
- difficult debugging;
- concurrency problems;
- unexpected side effects;
- fragile agent behavior.

### 13.5 Hook activation workflow

```text
Add hook definition
→ verify script exists
→ verify runtime dependency
→ review hook behavior
→ trust configuration
→ run smoke test
→ inspect output
→ enable in normal workflow
```

### 13.6 Hook evaluation

Add:

```text
eval/hooks/
├── event_cases.json
├── expected_outputs.json
└── run_hook_eval.py
```

Measure:

- activation correctness;
- runtime success;
- latency;
- duplicate activation;
- concurrency safety;
- failure behavior;
- sensitive-data leakage.

---

## 14. Proposed Repository Structure

```text
template_agent_build/
├── AGENTS.md
├── AGENTS.override.md.example
├── agent-skills.lock.json
│
├── .agents/
│   └── skills/
│       ├── repo-navigator/
│       ├── implement-change/
│       ├── debug-test-failure/
│       ├── review-change/
│       ├── task-audit/
│       ├── memory-maintenance/
│       ├── semantic-code-search/
│       └── source-understanding/
│
├── .codex/
│   ├── config.toml
│   ├── hooks.json
│   └── rules/
│       └── default.rules
│
├── docs/
│   └── agent/
│       ├── INDEX.md
│       ├── INSTRUCTION_HIERARCHY.md
│       ├── SKILLS_POLICY.md
│       ├── HOOKS_POLICY.md
│       ├── RULES_POLICY.md
│       ├── TOOLS.md
│       └── RESPONSE_STYLE.md
│
├── eval/
│   ├── instructions/
│   ├── skills/
│   ├── hooks/
│   └── rules/
│
└── scripts/
    ├── check_agents_budget.py
    ├── validate_agent_instructions.py
    ├── install_agent_skills.py
    ├── check_agent_skills.py
    ├── update_agent_skills.py
    ├── eval_skill_activation.py
    ├── validate_hooks.py
    └── validate_rules.py
```

---

## 15. Implementation Roadmap

## Phase P0 — Instruction Hygiene

### Objective

Make project instructions smaller, clearer, and measurable.

### Tasks

- [ ] Reduce root `AGENTS.md` to approximately 6–8 KiB.
- [ ] Add `## Response Style`.
- [ ] Add `## Instruction Hierarchy`.
- [ ] Move detailed tool workflows out of root `AGENTS.md`.
- [ ] Add `AGENTS.override.md.example`.
- [ ] Add live `AGENTS.override.md` to `.gitignore`.
- [ ] Add `scripts/check_agents_budget.py`.
- [ ] Add `make check-agent-budget`.
- [ ] Add CI validation for instruction size.

### Acceptance criteria

- Root `AGENTS.md` is ≤ 8 KiB.
- No tool-specific command catalog remains in root instructions.
- Override behavior is documented.
- CI detects byte-budget violations.
- Root instructions retain all non-negotiable project policies.

---

## Phase P1 — Skill Dependency System

### Objective

Make skills installable, versioned, discoverable, and testable.

### Tasks

- [ ] Audit current skills.
- [ ] Merge overlapping skills.
- [ ] Keep approximately five to eight primary skills.
- [ ] Add `agent-skills.lock.json`.
- [ ] Add skill version and dependency metadata.
- [ ] Add install, check, and update scripts.
- [ ] Validate recognized installation paths.
- [ ] Add activation test cases.
- [ ] Add dependency availability checks.

### Acceptance criteria

- Every required skill appears in the manifest.
- Every required skill is discoverable.
- Missing tool dependencies are reported clearly.
- Skill activation evals include positive and negative cases.
- No broad or ambiguous “general assistant” skill remains.

---

## Phase P2 — Rules and Security

### Objective

Separate command security policy from instructions and skills.

### Tasks

- [ ] Add `.codex/rules/default.rules`.
- [ ] Define allow, prompt, and forbidden categories.
- [ ] Add package-installation and network-access policies.
- [ ] Add destructive-command protection.
- [ ] Add secret-access protection.
- [ ] Add positive and negative rule cases.
- [ ] Add precedence collision tests.

### Acceptance criteria

- Safe validation commands can run without unnecessary prompts.
- Sensitive commands require approval.
- Destructive commands are forbidden.
- Rule behavior is covered by automated evaluation.
- Coding style guidance does not appear in command rules.

---

## Phase P3 — Minimal Hooks

### Objective

Add deterministic automation without creating excessive complexity.

### Tasks

- [ ] Add `.codex/hooks.json`.
- [ ] Implement `SessionStart` dependency checks.
- [ ] Implement `UserPromptSubmit` secret checks.
- [ ] Implement `Stop` configuration validation.
- [ ] Implement `SessionEnd` compact audit metrics.
- [ ] Add hook smoke tests.
- [ ] Document trust and activation requirements.
- [ ] Measure hook latency.

### Acceptance criteria

- Hooks activate only for intended events.
- Hook failures do not silently corrupt agent behavior.
- Hooks do not expose secrets.
- Hook configuration is validated.
- Added latency remains acceptable.
- No hook depends on execution order unless explicitly guaranteed.

---

## Phase P4 — Evaluation and Observability

### Objective

Prove that instructions, skills, rules, and hooks improve agent performance.

### Tasks

- [ ] Add instruction precedence test cases.
- [ ] Add skill activation precision and recall tests.
- [ ] Add rule-resolution tests.
- [ ] Add hook activation and latency tests.
- [ ] Log selected skills and missing dependencies.
- [ ] Track instruction-chain size.
- [ ] Track number of activated skills per task.
- [ ] Track false activations.
- [ ] Track hook failures.
- [ ] Track task completion and regression rates.

### Acceptance criteria

- Each mechanism has an evaluation suite.
- Failures are observable and actionable.
- Template changes can be regression-tested.
- Skill and instruction changes are not merged without passing evals.

---

## 16. Metrics

### Instruction metrics

- root instruction bytes;
- maximum nested chain bytes;
- duplicate instruction count;
- conflict count;
- truncation risk.

### Skill metrics

- installed skill count;
- required skill availability;
- activation precision;
- activation recall;
- collision rate;
- missing dependency rate;
- task success after activation.

### Rule metrics

- allowed command accuracy;
- unnecessary prompt rate;
- forbidden-command block rate;
- precedence correctness;
- false-positive block rate.

### Hook metrics

- activation success rate;
- hook latency;
- failure rate;
- duplicate execution rate;
- sensitive-data leakage incidents.

### Product-level metrics

- time to first successful task;
- task completion rate;
- number of files read per task;
- token use per task;
- command retry rate;
- agent configuration error rate;
- user trust and acceptance.

---

## 17. Main Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Too many skills | Routing confusion and prompt overhead | Limit core skills and test activation |
| Overly short instructions | Missing critical project constraints | Keep stable non-negotiable rules in root |
| Incorrect override use | Root instructions silently replaced | Use only example file and document behavior |
| Hooks run unexpectedly | Latency or side effects | Start with four minimal hooks and smoke-test |
| Rules block valid work | Reduced productivity | Add positive and negative eval cases |
| Skills copied but not installed | Runtime cannot discover them | Add manifest and installation checks |
| Skill dependencies missing | Skill activates but cannot execute | Validate dependencies before activation |
| Precedence misunderstood | Conflicting behavior | Add hierarchy document and conflict tests |
| Tool-specific instructions grow again | Root file becomes bloated | Enforce byte budget in CI |
| Security policy hidden in prose | Commands bypass intended restrictions | Put command policy in formal rules |

---

## 18. Definition of Done

This improvement plan is complete when:

- [ ] root `AGENTS.md` is within the internal byte budget;
- [ ] response style and precedence are documented;
- [ ] override behavior is supported safely;
- [ ] skills are versioned and dependency-aware;
- [ ] required skills can be installed and checked;
- [ ] skill activation has positive and negative evals;
- [ ] command rules are separated from project instructions;
- [ ] hooks are configured, trusted, and smoke-tested;
- [ ] each mechanism has regression evaluation;
- [ ] CI validates instruction budget, skills, hooks, and rules;
- [ ] documentation explains the full operating model.

---

## 19. Final Design Principle

```text
AGENTS.md tells the agent how to behave.

Skills teach the agent how to perform specialized work.

Tools provide external capabilities.

Hooks perform deterministic lifecycle automation.

Rules control which commands may execute.

Evals prove that the complete system behaves correctly.
```

The template should evolve from a collection of useful agent files into a coherent, dependency-aware, policy-controlled, and evaluation-driven agent operating system for software repositories.
