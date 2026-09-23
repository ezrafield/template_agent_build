import json
from pathlib import Path

from scripts import memory_lookup
from scripts.memory_evidence import capture_evidence


def write_index(root: Path, entries: list[dict]) -> str:
    path = root / ".agent/memory/index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"version": 1, "memories": entries})
    path.write_text(text, encoding="utf-8")
    return text


def entry(root: Path, identifier: str = "debugging", **changes) -> dict:
    card = f".agent/memory/{identifier}.md"
    (root / card).parent.mkdir(parents=True, exist_ok=True)
    (root / card).write_text("A reviewed memory card.\n", encoding="utf-8")
    value = {
        "id": identifier, "type": "procedural", "scope": "debugging", "path": card,
        "summary": "Reproduce failures and check nearby tests.", "keywords": ["failure", "tests"],
        "confidence": "medium", "last_verified": "2026-09-22", "source_task": ".agent/task.md",
    }
    value.update(changes)
    return value


def test_task_prose_with_source_paths_keeps_keyword_matches(tmp_path):
    query = r"fix src\api\routes.py error handling"
    first = entry(tmp_path, "api-errors", scope="api", summary="Check API error handling.", keywords=["error", "handling"])
    other = entry(tmp_path, "deploy", scope="release", summary="Release checklist.", keywords=["release"])
    original_index = write_index(tmp_path, [first, other])
    rendered = memory_lookup.render_lookup(tmp_path, query)
    assert "api-errors.md" in rendered
    assert "Release checklist" not in rendered
    assert (tmp_path / ".agent/memory/index.json").read_text(encoding="utf-8") == original_index


def test_memory_paths_with_spaces_are_still_precise(tmp_path):
    selected = entry(tmp_path, "api-errors", path=".agent/memory/api notes/error handling.md")
    unrelated = entry(tmp_path, "generic", summary="API notes about error handling.")
    write_index(tmp_path, [selected, unrelated])
    rendered = memory_lookup.render_lookup(tmp_path, ".agent/memory/api notes/error handling.md")
    assert ".agent/memory/api notes/error handling.md" in rendered
    assert "API notes about error handling" not in rendered
    assert "No matching memories" in memory_lookup.render_lookup(tmp_path, ".agent/memory/api notes/missing card.md")


def test_current_drift_and_missing_sources_are_reported_without_hashes_or_mutation(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("original\n", encoding="utf-8")
    item = entry(tmp_path, evidence=capture_evidence(tmp_path, ["source.md"]))
    original_index = write_index(tmp_path, [item])
    digest = item["evidence"][0]["sha256"]
    rendered = memory_lookup.render_lookup(tmp_path)
    assert "unchanged" in rendered and digest not in rendered and "sha256" not in rendered
    source.write_text("changed\n", encoding="utf-8")
    assert "needs-reverification" in memory_lookup.render_lookup(tmp_path)
    source.unlink()
    assert "missing-evidence" in memory_lookup.render_lookup(tmp_path)
    assert (tmp_path / ".agent/memory/index.json").read_text(encoding="utf-8") == original_index


def test_lookup_redacts_credentials_and_escapes_markdown(tmp_path):
    item = entry(tmp_path, summary='password="private words" token=private-token https://alice:private-password@example.test/ ![x](https://example.test/a) <script>')
    item["id"] = "api_key=private-id"
    write_index(tmp_path, [item])
    rendered = memory_lookup.render_lookup(tmp_path)
    assert "private" not in rendered
    assert "REDACTED" in rendered
    assert "![x]" not in rendered and "<script>" not in rendered
