# Agent Context Index

Use this file to choose the smallest useful context for the task.

## For Bug Fixes
Read:
1. `docs/agent/CONTEXT_ROUTER.md`
2. `docs/agent/CODEMAP.md`
3. Relevant module card in `docs/agent/module-cards/`
4. Related tests

Do not read:
- Full product docs
- Full architecture docs
- Unrelated modules

## For New API Endpoints
Read:
1. `docs/agent/module-cards/api.md`
2. `docs/specs/api-contracts.md`
3. Existing similar endpoint
4. Relevant service module card

## For Database Changes
Read:
1. `docs/agent/module-cards/database.md`
2. Relevant ADRs in `docs/adr/`
3. Existing migrations or model files
4. Related model tests

## For Frontend Changes
Read:
1. `docs/agent/module-cards/frontend.md`
2. `docs/product/USER_FLOWS.md`
3. Existing similar screen or component
4. Related tests

## For Refactors
Read:
1. `docs/agent/ARCHITECTURE.md`
2. Relevant module cards
3. Current tests
4. `docs/agent/PITFALLS.md`

## For Planning Or Product Questions
Read:
1. `.agents/skills/plan-evolution/SKILL.md`
2. Existing related records under `.agent/plans/`
3. `docs/product/PRD.md`
4. `docs/product/REQUIREMENTS.md`
5. `docs/product/USER_FLOWS.md`

## For Agent, Skill, Tool, Or MCP Changes
Read:
1. `docs/agent/AGENTS_AND_SKILLS.md`
2. `docs/agent/CODEX_CUSTOMIZATION.md` for instructions, skills, hooks, rules, trust, or evals
3. `docs/agent/TOOLS.md`
4. `docs/agent/MCPS.md`
5. `docs/agent/COMMAND_OUTPUT_POLICY.md` when command execution or output volume is affected
6. Relevant files under `.agents/skills/`, `.codex/templates/`, `.claude/agents/`, `.mcp/`, or `scripts/`

## For Long-Term Memory Changes
Read:
1. `docs/agent/MEMORY_POLICY.md`
2. `docs/agent/MEMORY_RETRIEVAL.md`
3. `docs/agent/MEMORY_PROMOTION_RULES.md`
4. `.agent/memory/index.json`
5. Relevant memory cards under `.agent/memory/semantic/` or `.agent/memory/procedural/`

## For Agent Kit Setup, Install, Or Audit
Read:
1. `agentkit-manifest.json`
2. `docs/agent/TOOLS.md`
3. `docs/agent/COMMAND_OUTPUT_POLICY.md`
4. `.agents/skills/agent-setup/SKILL.md`
5. `docs/agent/CODEX_CUSTOMIZATION.md`
6. Relevant installer, setup, audit, or hook files under `scripts/`, `.agent/`, `.codex/templates/`, or `.claude/hooks/`

## For Source Understanding Or Code Search
Read:
1. `docs/agent/CONTEXT_ROUTER.md`
2. `docs/agent/CODE_SEARCH.md`
3. `docs/agent/CODEMAP.md`
4. `docs/agent/SOURCE_UNDERSTANDING.md`
5. `docs/agent/module-cards/source-understanding.md`
6. `.understand-anything/README.md`
7. `.understand-anything/knowledge-graph.json` only through targeted search when it exists
