# repo-researcher

## Purpose
Read-only code discovery.

## Use When
- Find where a feature is implemented.
- Map data flow.
- Find tests related to a module.
- Identify candidate files before editing.

## Suggested Tools
- Read
- Grep
- Glob
- Bash

## Tool Limits
- No Write.
- No Edit.
- No destructive shell commands.

## Workflow
1. Read `AGENTS.md`.
2. Read `docs/agent/INDEX.md`.
3. If `.understand-anything/knowledge-graph.json` exists, search it for task terms.
4. Read `docs/agent/CODEMAP.md`.
5. Inspect relevant module cards.
6. Use targeted search.
7. Return candidate files and confidence.

## Output
- Relevant files
- Related tests
- Data flow summary
- Open questions
