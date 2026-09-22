import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from scripts import audit_memory_staleness, extract_task_memory, memory_evidence, validate_memory_links


def memory_root(tmp_path: Path, *, evidence: bool = False) -> tuple[Path, dict]:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/source.md").write_text("Reviewed source.\n", encoding="utf-8")
    (tmp_path / ".agent/memory").mkdir(parents=True)
    (tmp_path / ".agent/task.md").write_text("Original task.\n", encoding="utf-8")
    card = (
        "# Memory\n\nType: semantic\nScope: project\nConfidence: high\n"
        "Last verified: 2026-09-22\nSource task: .agent/task.md\n\n"
        "## When to use\nUse during reviews.\n\n## Content\nA reusable claim.\n\n"
        "## Related files\n- `docs/source.md`\n\n## Staleness triggers\nSource changes.\n"
    )
    (tmp_path / ".agent/memory/card.md").write_text(card, encoding="utf-8")
    entry = {
        "id": "lesson", "type": "semantic", "scope": "project",
        "path": ".agent/memory/card.md", "summary": "A lesson", "keywords": ["review"],
        "confidence": "high", "last_verified": "2026-09-22", "source_task": ".agent/task.md",
    }
    if evidence:
        entry["evidence"] = memory_evidence.capture_evidence(tmp_path, ["docs/source.md"])
    save_entry(tmp_path, entry)
    return tmp_path, entry


def save_entry(root: Path, entry: dict) -> None:
    (root / ".agent/memory/index.json").write_text(
        json.dumps({"version": 1, "memories": [entry]}), encoding="utf-8"
    )


def test_hash_normalizes_line_endings_but_preserves_text(tmp_path):
    source = tmp_path / "source.md"
    source.write_bytes("one\r\ntwø\rthree\n".encode("utf-8"))
    expected = hashlib.sha256("one\ntwø\nthree\n".encode("utf-8")).hexdigest()
    assert memory_evidence.source_sha256(tmp_path, "source.md") == expected
    source.write_bytes("one\ntwø\nthree\n".encode("utf-8"))
    assert memory_evidence.source_sha256(tmp_path, "source.md") == expected
    source.write_bytes("one \ntwø\nthree\n".encode("utf-8"))
    assert memory_evidence.source_sha256(tmp_path, "source.md") != expected


def test_legacy_memory_is_untracked_and_opt_in_strict_validation_fails(tmp_path):
    root, _ = memory_root(tmp_path)
    errors, statuses = validate_memory_links.validate(root)
    assert not errors
    assert statuses == ["lesson: untracked"]
    assert "missing-evidence" in " ".join(validate_memory_links.validate(root, ["lesson"])[0])
    assert validate_memory_links.main(["--root", str(root), "--require-evidence"]) == 1
    assert "Unknown memory id" in " ".join(validate_memory_links.validate(root, ["unknown"])[0])


def test_evidence_audit_detects_drift_and_missing_file_without_claiming_falsity(tmp_path):
    root, entry = memory_root(tmp_path, evidence=True)
    assert validate_memory_links.main(["--root", str(root), "--require-evidence", "lesson"]) == 0
    assert audit_memory_staleness.audit(root, date(2026, 9, 22)) == ([], ["lesson: unchanged"])
    (root / "docs/source.md").write_text("Changed source.\n", encoding="utf-8")
    report = memory_evidence.inspect_evidence(root, entry)
    assert report.status == "needs-reverification"
    assert "review the memory claim" in report.details[0]
    warnings, statuses = audit_memory_staleness.audit(root, date(2026, 9, 22))
    assert warnings and statuses == ["lesson: needs-reverification"]
    (root / "docs/source.md").unlink()
    assert memory_evidence.inspect_evidence(root, entry).status == "missing-evidence"


def test_legacy_windows_paths_remain_valid_without_relaxing_evidence_paths(tmp_path):
    root, entry = memory_root(tmp_path)
    card = root / entry["path"]
    card.write_text(card.read_text().replace(".agent/task.md", ".agent\\task.md").replace("docs/source.md", "docs\\source.md"), encoding="utf-8")
    entry["path"] = entry["path"].replace("/", "\\")
    entry["source_task"] = entry["source_task"].replace("/", "\\")
    save_entry(root, entry)
    assert validate_memory_links.validate(root) == ([], ["lesson: untracked"])
    assert audit_memory_staleness.audit(root, date(2026, 9, 22)) == ([], ["lesson: untracked"])
    entry["evidence"] = [{"path": "docs\\source.md", "sha256": "0" * 64}]
    assert memory_evidence.inspect_evidence(root, entry).status == "invalid-evidence"


def test_legacy_independently_dated_metadata_remains_compatible(tmp_path):
    root, entry = memory_root(tmp_path)
    entry["last_verified"] = "2026-09-21"
    save_entry(root, entry)
    assert validate_memory_links.validate(root) == ([], ["lesson: untracked"])


@pytest.mark.parametrize("path", ["../outside.md", "/absolute.md", "C:/secret.md", "docs\\source.md", ".env", "secrets/token.md", ".git/config", ".agent/memory/index.json"])
def test_unsafe_evidence_sources_are_rejected(tmp_path, path):
    report = memory_evidence.inspect_evidence(tmp_path, {"evidence": [{"path": path, "sha256": "0" * 64}]})
    assert report.status == "invalid-evidence"


def test_symlink_evidence_cannot_escape_repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    try:
        (root / "link.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is not available")
    with pytest.raises(memory_evidence.EvidenceError, match="outside"):
        memory_evidence.source_sha256(root, "link.md")


@pytest.mark.parametrize("evidence", [[], "wrong", [None], [{"path": "source.md", "sha256": "bad"}], [{"path": 7, "sha256": "0" * 64}], [{"path": "source.md", "sha256": "0" * 64, "extra": 1}]])
def test_malformed_evidence_is_not_accepted(tmp_path, evidence):
    assert memory_evidence.inspect_evidence(tmp_path, {"evidence": evidence}).status == "invalid-evidence"


def test_duplicate_evidence_and_unreadable_sources(tmp_path, monkeypatch):
    source = tmp_path / "source.md"
    source.write_bytes(b"normal")
    evidence = memory_evidence.capture_evidence(tmp_path, ["source.md"])
    assert memory_evidence.inspect_evidence(tmp_path, {"evidence": evidence * 2}).status == "invalid-evidence"
    for raw in (b"bad\xff", b"binary\0text"):
        source.write_bytes(raw)
        with pytest.raises(memory_evidence.EvidenceError):
            memory_evidence.source_sha256(tmp_path, "source.md")
    monkeypatch.setattr(memory_evidence, "MAX_SOURCE_BYTES", 2)
    source.write_bytes(b"large")
    with pytest.raises(memory_evidence.EvidenceError, match="exceeds"):
        memory_evidence.source_sha256(tmp_path, "source.md")


def test_audit_age_and_card_metadata_mismatch_are_actionable(tmp_path):
    root, entry = memory_root(tmp_path, evidence=True)
    warnings, statuses = audit_memory_staleness.audit(root, date(2027, 9, 22))
    assert "last verified" in " ".join(warnings)
    assert statuses == ["lesson: needs-reverification"]
    entry["last_verified"] = "2026-09-21"
    save_entry(root, entry)
    assert "Last verified does not match" in " ".join(validate_memory_links.validate(root)[0])
    entry["path"] = "../outside.md"
    save_entry(root, entry)
    assert "path traversal" in " ".join(validate_memory_links.validate(root)[0])


def test_candidate_fingerprints_are_explicitly_unreviewed(tmp_path):
    root, _ = memory_root(tmp_path)
    text = "# Task\n\n## Goal\nA useful lesson.\n\n## Files Inspected\n- `docs/source.md`\n- `../outside.md`\n"
    candidate = extract_task_memory.candidate_body(root / ".agent/task.md", text, root)
    assert "Last verified: TODO" in candidate
    assert "not verified claims" in candidate
    assert memory_evidence.source_sha256(root, "docs/source.md") in candidate
    assert "path traversal" in candidate


def test_invalid_index_is_reported_without_traceback(tmp_path):
    root, _ = memory_root(tmp_path)
    (root / ".agent/memory/index.json").write_text("[]", encoding="utf-8")
    assert validate_memory_links.main(["--root", str(root)]) == 1
    assert audit_memory_staleness.main(["--root", str(root)]) == 1
