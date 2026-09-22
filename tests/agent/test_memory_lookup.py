import json
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("query", ["debugging", "DEBUGGING", "failures", "tests", ".agent/memory/debugging.md", r".agent\memory\debugging.md"])
def test_exact_and_word_queries_find_metadata_without_loading_cards(tmp_path, query):
    first = entry(tmp_path)
    other = entry(tmp_path, "deploy", scope="release", summary="Release checklist.", keywords=["release"])
    write_index(tmp_path, [first, other])
    rendered = memory_lookup.render_lookup(tmp_path, query)
    assert "debugging.md" in rendered
    assert "Release checklist" not in rendered
    assert "A reviewed memory card" not in rendered
    assert "untracked" in rendered


def test_no_false_substring_match_and_empty_query_lists_all(tmp_path):
    write_index(tmp_path, [entry(tmp_path, "latest", scope="shipping", summary="Latest release.", keywords=["shipping"])])
    assert "No matching memories" in memory_lookup.render_lookup(tmp_path, "test")
    assert "Latest release" in memory_lookup.render_lookup(tmp_path)
    assert "No matching memories" in memory_lookup.render_lookup(tmp_path, ".agent/memory/missing.md")


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


def test_supplied_index_text_is_used_without_reading_index_again(tmp_path):
    snapshot = write_index(tmp_path, [entry(tmp_path)])
    (tmp_path / ".agent/memory/index.json").write_text("broken current index", encoding="utf-8")
    assert "debugging.md" in memory_lookup.render_lookup(tmp_path, index_text=snapshot)
    with pytest.raises(memory_lookup.MemoryLookupError, match="valid UTF-8 JSON"):
        memory_lookup.render_lookup(tmp_path)


def test_legacy_windows_card_and_source_paths_remain_compatible(tmp_path):
    item = entry(tmp_path)
    item["path"] = item["path"].replace("/", "\\")
    item["source_task"] = item["source_task"].replace("/", "\\")
    write_index(tmp_path, [item])
    rendered = memory_lookup.render_lookup(tmp_path)
    assert ".agent/memory/debugging.md" in rendered
    assert "untracked" in rendered
    assert "card missing" not in rendered


@pytest.mark.parametrize("payload", ["invalid", "[]", '{"version":2,"memories":[]}', '{"version":true,"memories":[]}', '{"version":1,"memories":{}}', '{"version":1,"memories":[null]}'])
def test_malformed_index_fails_clearly(tmp_path, payload):
    with pytest.raises(memory_lookup.MemoryLookupError):
        memory_lookup.render_lookup(tmp_path, index_text=payload)


@pytest.mark.parametrize("change", [{"keywords": "not-a-list"}, {"summary": None}, {"last_verified": "yesterday"}, {"path": "../secret.md"}, {"path": ".env"}, {"source_task": "C:/outside.md"}])
def test_invalid_metadata_and_unsafe_paths_fail_without_echoing_values(tmp_path, change):
    item = entry(tmp_path, **change)
    write_index(tmp_path, [item])
    with pytest.raises(memory_lookup.MemoryLookupError, match="Memory entry 1") as error:
        memory_lookup.render_lookup(tmp_path)
    assert "secret.md" not in str(error.value)
    assert "outside.md" not in str(error.value)


def test_duplicate_ids_fail_even_when_query_would_hide_one(tmp_path):
    item = entry(tmp_path)
    write_index(tmp_path, [item, dict(item)])
    with pytest.raises(memory_lookup.MemoryLookupError, match="repeats a memory ID"):
        memory_lookup.render_lookup(tmp_path, "not-matching")


def test_secret_like_values_are_redacted_before_truncation_and_markdown_is_plain(tmp_path):
    item = entry(tmp_path, summary='password="private words" token=private-token https://alice:private-password@example.test/ ![x](https://example.test/a) <script>')
    item["id"] = "api_key=private-id"
    write_index(tmp_path, [item])
    rendered = memory_lookup.render_lookup(tmp_path)
    assert "private" not in rendered
    assert "REDACTED" in rendered
    assert "![x]" not in rendered and "<script>" not in rendered
    item["summary"] = "-----BEGIN PRIVATE KEY-----\nprivate body\n-----END PRIVATE KEY-----"
    write_index(tmp_path, [item])
    assert "private body" not in memory_lookup.render_lookup(tmp_path)


def test_malformed_evidence_is_labeled_and_details_are_not_dumped(tmp_path):
    write_index(tmp_path, [entry(tmp_path, evidence=[{"path": "password=private", "sha256": "bad"}])])
    rendered = memory_lookup.render_lookup(tmp_path)
    assert "invalid-evidence" in rendered and "private" not in rendered


def test_output_limits_report_omissions_and_api_rejects_unbounded_inputs(tmp_path):
    entries = [entry(tmp_path, f"memory-{index}", summary="&|*[]" * 700) for index in range(25)]
    write_index(tmp_path, entries)
    rendered = memory_lookup.render_lookup(tmp_path, limit=20)
    assert len(rendered) <= memory_lookup.MAX_OUTPUT_CHARS
    assert "Results omitted" in rendered
    assert "unchanged" not in rendered
    for limit in (0, -1, 21, True):
        with pytest.raises(memory_lookup.MemoryLookupError, match="limit"):
            memory_lookup.render_lookup(tmp_path, limit=limit)
    with pytest.raises(memory_lookup.MemoryLookupError, match="query"):
        memory_lookup.render_lookup(tmp_path, "x" * 513)
    with pytest.raises(memory_lookup.MemoryLookupError, match="input limit"):
        memory_lookup.render_lookup(tmp_path, index_text="x" * 1_000_001)


def test_card_absence_is_visible_and_cli_errors_do_not_echo_index_data(tmp_path, capsys):
    item = entry(tmp_path)
    write_index(tmp_path, [item])
    (tmp_path / item["path"]).unlink()
    assert memory_lookup.main(["--root", str(tmp_path)]) == 0
    assert "card missing" in capsys.readouterr().out
    (tmp_path / ".agent/memory/index.json").write_text("password=private", encoding="utf-8")
    assert memory_lookup.main(["--root", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "private" not in captured.out + captured.err
    assert "valid UTF-8 JSON" in captured.err


def test_evidence_io_is_bounded_and_argument_errors_are_redacted(tmp_path, capsys):
    item = entry(tmp_path, evidence=[{"path": "source.md", "sha256": "0" * 64}] * 129)
    write_index(tmp_path, [item])
    with pytest.raises(memory_lookup.MemoryLookupError, match="too many evidence"):
        memory_lookup.render_lookup(tmp_path)
    with pytest.raises(SystemExit) as error:
        memory_lookup.main(["--limit", "token=private-value"])
    assert error.value.code == 2
    assert "private-value" not in capsys.readouterr().err
