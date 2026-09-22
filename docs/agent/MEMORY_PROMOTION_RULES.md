# Memory Promotion Rules

Promotion is manual. Generated candidates are drafts until reviewed and indexed.

## Promotion Flow

1. Finish a meaningful task and update its `.agent/tasks/` log.
2. Run `make extract-task-memory TASK=.agent/tasks/<task>.md`.
3. Review the candidate in `.agent/memory/candidates/`.
4. Delete secrets, private data, noisy details, and unverified claims.
5. Move durable facts into `.agent/memory/semantic/` or reusable workflows into `.agent/memory/procedural/`.
6. Capture fingerprints of the reviewed source files with
   `python scripts/memory_evidence.py <source-path> [<source-path> ...]` and add the
   resulting non-empty `evidence` list to `.agent/memory/index.json`.
7. Record the actual verification date in the card and index. Keep original task
   provenance; link a separate `verification_record` when re-verifying an old card.
8. Run `python scripts/validate_memory_links.py --require-evidence <memory-id>`,
   then `make audit-memory`.

## Promote When

- The lesson is likely to help future tasks.
- It is more compact than the original task log.
- It names when to use the lesson.
- It includes related files or docs that can be re-verified.
- It includes confidence and staleness triggers.
- Newly promoted or re-verified entries include source fingerprints after review.

## Do Not Promote When

- The information is a one-off task detail.
- The claim depends on stale code that was not verified.
- The card would expose secrets or private data.
- The guidance is overbroad, such as "always edit this file when tests fail."

## Reviewing Drift

Generated candidates may contain unreviewed fingerprints of inspected files.
Select only sources that support the final claim, review their current contents,
and capture them again before promotion. Never refresh hashes simply to make an
audit pass. `needs-reverification` means inspect the change, then retain, revise,
or retire the claim. Existing entries without fingerprints remain `untracked`
until deliberately reviewed; no automatic migration or promotion occurs.

## Confidence

- High: verified against current code, tests, or docs.
- Medium: useful and plausible, but may need confirmation in nearby files.
- Low: keep as a candidate or task note; do not promote unless clearly marked and useful.
