# Plan: Single Agent Entrypoint

## Metadata

- Created: 2026-09-23
- Updated: 2026-09-23
- Kind: migration
- Status: completed
- Owners: user and AI
- Version / Relation: follows `../completed/2026-09-23-daily-ai-change-log.md`; baseline `4ef3d6d` plus daily-log changes

## Goal

Use AGENTS.md across supported hosts; remove root and sample-source CLAUDE.md.

## Why This Strategy

One authoritative entrypoint avoids duplicated rules and context. Claude Code
now supports it natively: https://code.claude.com/docs/en/memory#agents-md.

## Scope

Setup, installer migration, validators, active documentation, reviewed memory,
and today's log. Preserve unrelated changes, historical records, and project-owned
instruction text during updates. Keep existing optional Claude agents/hooks.

## Success Signals

Fresh installs/setup create only AGENTS.md. Updates remove obsolete managed
Claude instructions with backups and retain custom text. Relevant checks pass
within the existing 49-case budget; native-support requirements are documented.

## Risks And Assumptions

Native support is version/session-dependent. Existing personal or parent-folder
instructions/settings are outside this repository migration.

## Verification

- Asset/docs validation and strict six-card memory checks pass without CLAUDE.md.
- Temporary setup probe creates only AGENTS.md, retains the daily-log rule, and
  preserves existing instructions. Root-side independent review found no defect.
- Installer suite: five passed, one Windows symlink-creation skip. Full pytest:
  38 passed, one skip in 3.02s (39 collected, within the 49-case cap).
- Compilation and final asset/docs/memory checks pass. Independent consolidated
  review found no material findings; no re-review was required.

## Outcome And Evidence

- Removed both redundant entrypoints and moved the sample source's unique rule
  into src/AGENTS.md. Setup, manifest, validators and current guidance agree.
- Kept historical records intact; the remaining hook match deliberately handles
  project-owned legacy files. No replacement wrapper, settings file, or service.
- Claude CLI is unavailable on PATH here; native behavior is documented from
  Anthropic's current source, not claimed as a live local test.
- Update migration backs up before removing a uniquely marked legacy kit block;
  preserves custom bytes and uncertain/unmanaged files, with migration guidance.
  Two focused regressions cover user-text preservation and symlink boundaries;
  existing lifecycle tests cover fresh/setup/pure-managed migration and ownership.

## Reflection

- User mindset/strategy learning: shared standards should reduce maintenance.
- AI workflow/prompt/context learning: changing a merge-file list requires
  reviewing old ownership records, not just deleting the template source.
- What worked: a narrow migration kept the single-entrypoint design compatible
  with existing installations without copying user-specific rules automatically.
- Remaining limit: native Claude loading and real symlink behavior need a
  suitable runtime; offline checks do not establish those live results.
