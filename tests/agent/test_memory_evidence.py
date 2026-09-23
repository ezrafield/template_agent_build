import hashlib
import json
from datetime import date
from pathlib import Path

from scripts import audit_memory_staleness, memory_evidence, validate_memory_links


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


def test_unsafe_evidence_traversal_is_rejected(tmp_path):
    path = "../outside.md"
    report = memory_evidence.inspect_evidence(tmp_path, {"evidence": [{"path": path, "sha256": "0" * 64}]})
    assert report.status == "invalid-evidence"
