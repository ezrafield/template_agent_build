# Plan: Template Diagram Guide

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: plan
- Status: completed
- Owners: user and AI
- Version / Relation: follows `../completed/2026-09-23-single-agent-entrypoint.md`

## Goal

One readable Markdown guide showing current architecture, routing, workflow,
and how the coding assistant coordinates tasks.

## Why This Strategy

Use small Mermaid diagrams and source links; distinguish context selection from
execution and optional experiments without duplicating operational manuals.

## Scope

One guide, a README link, and today's change-log entry. No runtime or test changes.

## Success Signals

Diagrams agree with current scripts/policies, links resolve, and the guide stays
outside mandatory context. Readers can identify the coordinator and optional paths.

## Risks And Assumptions

Mermaid needs a supporting Markdown viewer; adjacent prose remains readable.
Workflow arrows describe agent instructions, not an autonomous scheduling service.

## Verification

- Independent source/diagram review found no material findings.
- Four Mermaid blocks and Markdown fences checked; local links resolve.
  Diagram syntax reviewed by inspection; no Mermaid renderer was run.
- Both routing examples match the current classifier. Docs/assets validation
  and whitespace checks pass. No runtime changes or new tests.

## Outcome And Evidence

`docs/agent/TEMPLATE_MAP.md` provides four diagrams with source links. README
links to it; no required route or instruction entrypoint was expanded.

## Reflection

- User mindset/strategy learning: show the system visually before more detail.
- AI workflow/prompt/context learning: separate the host's coordination from
  the compiler's context selection, and show optional advice without authority.
