# Memory Policy

Long-term memory helps agents reuse durable lessons without reading old task logs.
It is guidance, not source of truth.

## Memory Types

| Type | Meaning | Location |
| --- | --- | --- |
| Semantic | Stable facts, conventions, and decisions | `.agent/memory/semantic/` |
| Procedural | Reusable workflows and playbooks | `.agent/memory/procedural/` |
| Episodic | Raw task logs and audit trails | `.agent/tasks/` |

## Authority

Use memory to choose likely files, workflows, commands, and risks. Before editing,
verify memory against current source files, tests, and docs. If memory conflicts
with the repository, the repository wins.

## Safety

Never promote:

- secrets, credentials, tokens, or private keys
- customer data or private user content
- raw stack traces containing sensitive paths or data
- one-off debugging noise
- claims that were not verified
- guidance that says to always edit a specific file when the real issue may vary

## Card Requirements

Promoted memory cards should include:

- `Type`
- `Scope`
- `Confidence`
- `Last verified`
- `Source task`
- `When to use`
- `Content` or `Procedure`
- `Related files`
- `Staleness triggers`

## Evidence Contract (v0.5)

The index remains version `1`. Existing entries without `evidence` remain valid
and are reported as `untracked`; they still need manual source verification.
Newly promoted or re-verified entries must include a non-empty `evidence` list:

```json
{"path": "docs/agent/MEMORY_POLICY.md", "sha256": "<64 lowercase hexadecimal characters>"}
```

Each item names a reviewed repository-relative UTF-8 text file and its SHA-256.
Hashing converts CRLF and lone CR newlines to LF, then encodes UTF-8; all other
text is preserved. This prevents Windows checkout newline changes from looking
like source drift. Evidence reads reject traversal, paths outside the repository,
sensitive paths, binary/non-UTF-8 files, files over 1,000,000 bytes, and the memory
index itself. Use forward slashes. Do not hash the index recursively or record
secrets as evidence.

After reviewing claims against current sources, capture the reviewed paths with:

```bash
python scripts/memory_evidence.py docs/agent/MEMORY_POLICY.md
python scripts/validate_memory_links.py --require-evidence <memory-id>
```

The capture command prints a list for manual inclusion in the entry; it does not
update cards or promote memory. `--require-evidence` without IDs checks every
entry. Normal validation and audits remain compatible with untracked legacy cards.

Audit statuses are `unchanged`, `untracked`, `needs-reverification`,
`missing-evidence`, or `invalid-evidence`. A changed fingerprint means a reviewer
must check the claim; it does not establish that the claim is false. Matching
fingerprints establish unchanged sources, not semantic truth. Missing, invalid,
drifted, or over-age tracked memory fails the audit until reviewed or retired.

Preserve historical `source_task` values. If provenance was only a scaffold
reference, say so; do not invent a past task. An optional `verification_record`
path in the index and matching `Verification record` field in the card can link
the current review separately. Update `last_verified` and `Last verified` only
after review, and keep both dates synchronized. A generated candidate is not a
verification event.
