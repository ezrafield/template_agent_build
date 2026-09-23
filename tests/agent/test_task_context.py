import hashlib
import json
from pathlib import Path

from scripts import task_context_engine as engine

ROOT = Path(__file__).resolve().parents[2]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def route_manifest(
    root: Path,
    *,
    required: list[dict] | None = None,
    optional: list[dict] | None = None,
    max_docs: int = 10,
    max_chars: int = 40000,
) -> None:
    write(root / "docs" / "agent" / "INDEX.md", "## Primary Route\n\n## General Route\n")
    payload = {
        "schema_version": 1,
        "index_path": "docs/agent/INDEX.md",
        "defaults": {
            "max_docs": max_docs,
            "max_chars": max_chars,
            "search_content": "all",
            "search_limit": 5,
            "selection_order": [
                "routed-required",
                "routed-optional",
                "advisory-search",
            ],
        },
        "exclude_globs": [".agent/context-cache/**"],
        "routes": [
            {
                "id": "primary",
                "index_heading": "Primary Route",
                "triggers": ["feature", "same score"],
                "required": required or [],
                "optional": optional or [],
            },
            {
                "id": "general",
                "index_heading": "General Route",
                "triggers": [],
                "required": [],
                "optional": [],
            },
        ],
    }
    write(root / "docs" / "agent" / "context-routes.json", json.dumps(payload))


def test_mixed_workflows_report_ambiguity_but_explicit_override_does_not() -> None:
    task = "Review this diff and fix the failing API test"
    result = engine.build_task_context(task, ROOT, use_search=False)
    assert any("Ambiguous route" in warning and "code-review" in warning and "bug-fix" in warning
               for warning in result.warnings)
    assert "Ambiguous route" in engine.render_explanation(result)
    assert "Ambiguous route" in engine.render_compact_markdown(result)
    overridden = engine.build_task_context(task, ROOT, route_id="api-endpoint", use_search=False)
    assert overridden.route_id == "api-endpoint"
    assert not any("Ambiguous route" in warning for warning in overridden.warnings)


def test_explicit_review_of_refactor_retains_review_context() -> None:
    task = "Code review this refactor"
    result = engine.build_task_context(task, ROOT, use_search=False)
    assert result.route_id == "code-review"
    assert ".agents/skills/code-review/SKILL.md" in {source.path for source in result.selected}
    override = engine.build_task_context(task, ROOT, route_id="refactor", use_search=False)
    assert override.route_id == "refactor"
    assert not any("Ambiguous route" in warning for warning in override.warnings)


def test_required_sources_precede_optional_and_advisory_sources(tmp_path: Path) -> None:
    write(tmp_path / "required.md", "# Required\n\nrequired context\n")
    write(tmp_path / "optional-feature.md", "# Optional feature\n\nfeature details\n")
    write(tmp_path / "search.md", "one\ntwo\nthree\n")
    route_manifest(
        tmp_path,
        required=[{"path": "required.md", "category": "contract"}],
        optional=[{"path": "optional-feature.md", "category": "optional"}],
    )

    def search(task: str, root: Path, content: str, limit: int) -> engine.SearchOutcome:
        return engine.SearchOutcome(
            status="ok",
            results=[
                engine.SearchResult("required.md", 1, 1, 99.0),
                engine.SearchResult("search.md", 2, 3, 10.0),
            ],
        )

    result = engine.build_task_context("feature work optional-feature.md", tmp_path, search_provider=search)

    assert [item.path for item in result.selected] == [
        "required.md",
        "optional-feature.md",
        "search.md",
    ]
    assert [item.origin for item in result.selected] == [
        "routed-required",
        "routed-optional",
        "advisory-search",
    ]
    assert any(item.path == "required.md" and item.reason == "duplicate_path" for item in result.dropped)
    assert result.selected[-1].excerpt == "two\nthree"


def test_document_and_character_budgets_are_enforced(tmp_path: Path) -> None:
    write(tmp_path / "required.md", "R" * 100)
    write(tmp_path / "optional-feature.md", "feature optional")
    write(tmp_path / "search.md", "search result")
    route_manifest(
        tmp_path,
        required=[{"path": "required.md", "category": "required"}],
        optional=[{"path": "optional-feature.md", "category": "optional"}],
        max_docs=1,
        max_chars=20,
    )

    def search(task: str, root: Path, content: str, limit: int) -> engine.SearchOutcome:
        return engine.SearchOutcome(
            status="ok", results=[engine.SearchResult("search.md", 1, 1, 1.0)]
        )

    result = engine.build_task_context("feature", tmp_path, search_provider=search)

    assert len(result.selected) == 1
    assert result.selected_chars == 20
    assert result.selected[0].truncated is True
    assert any("document_budget_exhausted" == item.reason for item in result.dropped)
    assert any("Truncated context" in warning for warning in result.warnings)


def test_secret_files_are_blocked_and_inline_assignments_are_redacted(tmp_path: Path) -> None:
    write(tmp_path / ".env", "TOKEN=do-not-read\n")
    write(tmp_path / ".env.production", "TOKEN=also-do-not-read\n")
    write(tmp_path / "client.pem", "certificate\n")
    write(tmp_path / "safe.md", "password=visible-value\nhttps://user:pass@example.test/path\n")
    route_manifest(
        tmp_path,
        required=[{"path": "safe.md", "category": "required"}],
    )

    def search(task: str, root: Path, content: str, limit: int) -> engine.SearchOutcome:
        return engine.SearchOutcome(
            status="ok",
            results=[
                engine.SearchResult(".env", 1, 1, 3.0),
                engine.SearchResult(".env.production", 1, 1, 2.0),
                engine.SearchResult("client.pem", 1, 1, 1.0),
            ],
        )

    result = engine.build_task_context("feature token=task-secret", tmp_path, search_provider=search)

    assert "visible-value" not in result.selected[0].excerpt
    assert "pass@example" not in result.selected[0].excerpt
    assert "<REDACTED-SECRET>" in result.selected[0].excerpt
    assert result.task == "feature token=<REDACTED-SECRET>"
    assert any(item.path == ".env" and item.reason.startswith("unsafe") for item in result.dropped)
    assert any(item.path == ".env.production" and item.reason.startswith("unsafe") for item in result.dropped)
    assert any(item.path == "client.pem" and item.reason.startswith("unsafe") for item in result.dropped)


def test_expansion_merges_ranges_without_repeating_required_lines(tmp_path: Path) -> None:
    write(tmp_path / "guide.md", "# Guide\n## Required\nrequired fact\n## Extra\nextra fact\nlast fact\n")
    route_manifest(tmp_path, required=[{
        "path": "guide.md", "category": "guide", "sections": ["Required"],
    }], max_docs=1)
    original = engine.build_task_context("feature", tmp_path, use_search=False).selected[0].excerpt
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False,
        expand_sources=[("guide.md", 2, 5), ("./guide.md", 4, 6), ("guide.md", 2, 5)],
        reason="Read the missing fact",
    )

    assert len(result.selected) == 1
    source = result.selected[0]
    assert source.excerpt.startswith(original)
    assert source.excerpt.count("required fact") == 1
    assert source.excerpt.count("extra fact") == 1
    assert source.excerpt.count("last fact") == 1
    assert source.selection_reason == "required_route+explicit_expansion"
    assert source.line_ranges == [(2, 6)]
    assert result.expansion_notes == ["`guide.md` lines 2-5, 4-6: included."]


def test_expansion_reuses_safety_exclusions_and_range_validation(tmp_path: Path) -> None:
    write(tmp_path / "safe.md", "one\ntwo\nthree\n")
    write(tmp_path / ".env", "TOKEN=must-not-read\n")
    write(tmp_path / ".agent/context-cache/cached.md", "stale text\n")
    route_manifest(tmp_path)
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False, reason="Check missing facts",
        expand_sources=[("../outside.md", 1, 1), ("C:/outside.md", 1, 1), (".env", 1, 1),
                        (".agent/context-cache/cached.md", 1, 1), ("absent.md", 1, 1),
                        ("safe.md", 0, 2), ("safe.md", 3, 2), ("safe.md", 4, 5), ("safe.md", 2, 99)],
    )
    assert [source.excerpt for source in result.selected] == ["two\nthree"]
    assert any(item.reason == "excluded_by_route" for item in result.dropped)
    assert sum(item.reason.startswith("unsafe:") for item in result.dropped) == 3
    assert sum(item.reason.startswith("invalid_expansion_range") for item in result.dropped) == 3
    assert any("Clipped expansion range" in warning for warning in result.warnings)
    assert "must-not-read" not in engine.render_markdown(result)


def test_expansion_identity_is_normalized_and_always_rereads_local_source(tmp_path: Path) -> None:
    write(tmp_path / "nested/extra.md", "one\ntwo\nthree\n")
    route_manifest(tmp_path)
    basic = engine.build_task_context("Feature Work", tmp_path, use_search=False)
    first = engine.build_task_context(
        "Feature Work", tmp_path, use_search=False,
        expand_sources=[("nested\\extra.md", 1, 2), ("nested/extra.md", 2, 3)], reason="Missing fact",
    )
    destination = engine.materialize_bundle(tmp_path, first)
    destination.write_text("malicious old cache\n", encoding="utf-8")
    write(tmp_path / "nested/extra.md", "one\nupdated\nthree\n")
    second = engine.build_task_context(
        " feature   work ", tmp_path, use_search=False,
        expand_sources=[("nested/extra.md", 2, 3), ("nested/extra.md", 1, 2)], reason="Missing   fact",
    )
    different_reason = engine.build_task_context(
        "feature work", tmp_path, use_search=False,
        expand_sources=[("nested/extra.md", 1, 3)], reason="Another fact",
    )
    different_range = engine.build_task_context(
        "feature work", tmp_path, use_search=False,
        expand_sources=[("nested/extra.md", 1, 2)], reason="Missing fact",
    )
    assert basic.task_hash == engine.task_hash("feature work")
    assert first.task_hash == second.task_hash != basic.task_hash
    assert different_reason.task_hash != second.task_hash != different_range.task_hash
    assert first.selected[0].source_hash != second.selected[0].source_hash
    assert second.selected[0].excerpt == "one\nupdated\nthree"
    assert engine.materialize_bundle(tmp_path, second) == destination
    assert "malicious" not in destination.read_text(encoding="utf-8")
    assert list(destination.parent.iterdir()) == [destination]


def test_named_definition_precedes_early_comments_and_references(tmp_path: Path) -> None:
    symbol = "_calculate_total"
    source = ("# invoice commentary\n" * 160 + f"# {symbol} reference\n" * 110
              + f"def {symbol}():\n    token='not-for-output'\n    return 42\n" + "# later unrelated\n" * 400)
    write(tmp_path / "helpers.py", source)
    route_manifest(tmp_path, optional=[{"path": "helpers.py", "category": "test"}])
    result = engine.build_task_context(f"feature inspect {symbol}() invoice", tmp_path, use_search=False)
    selected = result.selected[0]
    assert selected.excerpt.startswith(f"def {symbol}():")
    assert "not-for-output" not in selected.excerpt
    assert selected.char_count <= engine.OPTIONAL_EXCERPT_CHARS
    assert len(selected.excerpt.splitlines()) <= engine.OPTIONAL_EXCERPT_LINES
    assert selected.source_hash == hashlib.sha256((tmp_path / "helpers.py").read_bytes()).hexdigest()
    assert selected.line_ranges[0][0] > 1
    assert any("remaining content omitted" in warning for warning in result.warnings)
    covered = [line for start, end in selected.line_ranges for line in range(start, end + 1)]
    assert len(covered) == len(set(covered))


def test_compact_complete_budget_prioritizes_required_text_and_discloses_omissions(tmp_path: Path) -> None:
    write(tmp_path / "required.md", "Required fact. " * 15)
    write(tmp_path / "payments.md", "Optional payments detail. " * 45)
    route_manifest(tmp_path, required=[{"path": "required.md", "category": "required"}],
                   optional=[{"path": "payments.md", "category": "optional"}], max_chars=1600)
    result = engine.build_task_context("feature payments", tmp_path, use_search=False)
    rendered = engine.render_compact_markdown(result)
    assert len(rendered) <= result.max_chars
    assert result.selected[0].excerpt in rendered
    assert "Clipped in compact view" in rendered or "Omitted from compact view" in rendered
    for source in result.selected:
        assert source.path in rendered and source.source_hash[:12] in rendered
    assert "complete audit may be larger" in engine.render_markdown(result)
    assert len(engine.render_markdown(result)) > result.max_chars
