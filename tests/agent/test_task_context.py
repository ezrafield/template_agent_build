import json
import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import task_context
from scripts import task_context_engine as engine
from eval.context import run_task_context_eval


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


def no_results(task: str, root: Path, content: str, limit: int) -> engine.SearchOutcome:
    return engine.SearchOutcome(status="ok")


def test_classification_fallback_and_explicit_override(tmp_path: Path) -> None:
    route_manifest(tmp_path)
    manifest, _ = engine.load_route_manifest(tmp_path)

    assert engine.classify_route("Implement a feature", manifest)["id"] == "primary"
    assert engine.classify_route("Unclassified task", manifest)["id"] == "general"
    assert engine.classify_route("Unclassified task", manifest, "primary")["id"] == "primary"
    with pytest.raises(engine.TaskContextError, match="Unknown route"):
        engine.classify_route("task", manifest, "missing")


def test_classification_ties_use_manifest_order(tmp_path: Path) -> None:
    route_manifest(tmp_path)
    path = tmp_path / "docs" / "agent" / "context-routes.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["routes"].insert(
        1,
        {
            "id": "secondary",
            "index_heading": "Secondary Route",
            "triggers": ["feature"],
            "required": [],
            "optional": [],
        },
    )
    write(tmp_path / "docs" / "agent" / "INDEX.md", "## Primary Route\n\n## Secondary Route\n\n## General Route\n")
    write(path, json.dumps(payload))

    manifest, _ = engine.load_route_manifest(tmp_path)

    assert engine.classify_route("feature", manifest)["id"] == "primary"


def test_route_manifest_requires_index_sync(tmp_path: Path) -> None:
    route_manifest(tmp_path)
    write(tmp_path / "docs" / "agent" / "INDEX.md", "## Primary Route\n")

    errors = engine.validate_route_manifest(tmp_path)

    assert any("General Route" in error for error in errors)


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


def test_windows_search_paths_are_normalized_and_content_is_reread(tmp_path: Path) -> None:
    write(tmp_path / "nested" / "feature.md", "line one\ntrusted local line\nline three\n")
    route_manifest(tmp_path)

    def search(task: str, root: Path, content: str, limit: int) -> engine.SearchOutcome:
        return engine.SearchOutcome(
            status="ok",
            results=[engine.SearchResult("nested\\feature.md", 2, 2, 1.0)],
        )

    result = engine.build_task_context("feature", tmp_path, search_provider=search)

    assert result.selected[0].path == "nested/feature.md"
    assert result.selected[0].excerpt == "trusted local line"


def test_h2_section_slicing_and_missing_section_warning(tmp_path: Path) -> None:
    write(
        tmp_path / "guide.md",
        "# Guide\n\nIntro\n\n## Flow\n\nKeep this.\n\n## Failure\n\nSkip this.\n",
    )
    route_manifest(
        tmp_path,
        required=[
            {
                "path": "guide.md",
                "category": "guide",
                "sections": ["Flow", "Missing"],
            }
        ],
    )

    result = engine.build_task_context("feature", tmp_path, use_search=False)

    assert "Keep this." in result.selected[0].excerpt
    assert "Skip this." not in result.selected[0].excerpt
    assert result.selected[0].sections == ["Flow"]
    assert any("Section `Missing`" in warning for warning in result.warnings)


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


def test_missing_required_and_unsafe_search_paths_are_warning_only(tmp_path: Path) -> None:
    route_manifest(
        tmp_path,
        required=[{"path": "missing.md", "category": "required"}],
    )

    def search(task: str, root: Path, content: str, limit: int) -> engine.SearchOutcome:
        return engine.SearchOutcome(
            status="ok",
            results=[
                engine.SearchResult("../outside.md", 1, 1, 2.0),
                engine.SearchResult("C:\\outside.md", 1, 1, 1.0),
            ],
        )

    result = engine.build_task_context("feature", tmp_path, search_provider=search)

    assert result.selected == []
    assert any("Required context not found" in warning for warning in result.warnings)
    assert any("parent traversal" in warning for warning in result.warnings)
    assert any("absolute paths" in warning for warning in result.warnings)
    assert result.gaps


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


def test_symlink_escape_is_blocked_when_supported(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    write(outside, "outside\n")
    link = tmp_path / "linked.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation is unavailable on this platform.")
    route_manifest(tmp_path, required=[{"path": "linked.md", "category": "required"}])

    result = engine.build_task_context("feature", tmp_path, use_search=False)

    assert result.selected == []
    assert any("outside the repository" in warning for warning in result.warnings)


def test_unavailable_and_malformed_semble_are_non_blocking(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(engine.run_agent_tool, "find_tool", lambda tool, env: None)
    unavailable = engine.run_semble_search("task", tmp_path, "all", 5)
    assert unavailable.status == "unavailable"

    monkeypatch.setattr(engine.run_agent_tool, "find_tool", lambda tool, env: "semble")

    class Completed:
        returncode = 0
        stdout = "not-json"
        stderr = ""

    monkeypatch.setattr(engine.subprocess, "run", lambda *args, **kwargs: Completed())
    malformed = engine.run_semble_search("task", tmp_path, "all", 5)
    assert malformed.status == "error"
    assert any("invalid JSON" in warning for warning in malformed.warnings)


def test_atomic_materialization_reuses_normalized_task_hash(tmp_path: Path) -> None:
    write(tmp_path / "required.md", "first\n")
    route_manifest(tmp_path, required=[{"path": "required.md", "category": "required"}])
    first = engine.build_task_context("  Feature   Work ", tmp_path, use_search=False)
    first_path = engine.materialize_bundle(tmp_path, first)
    write(tmp_path / "required.md", "second\n")
    second = engine.build_task_context("feature work", tmp_path, use_search=False)
    second_path = engine.materialize_bundle(tmp_path, second)

    assert first_path == second_path
    assert "second" in second_path.read_text(encoding="utf-8")
    assert "first" not in second_path.read_text(encoding="utf-8")
    assert not list(second_path.parent.glob("*.tmp"))


def test_markdown_and_explanation_include_trace_hashes_and_budget(tmp_path: Path) -> None:
    write(tmp_path / "required.md", "required\n")
    route_manifest(tmp_path, required=[{"path": "required.md", "category": "required"}])
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False, generated_at="2026-08-15T00:00:00Z"
    )

    markdown = engine.render_markdown(result)
    explanation = engine.render_explanation(result)

    assert "## Selected Sources" in markdown
    assert "## Dropped Candidates" in markdown
    assert result.selected[0].source_hash in markdown
    assert "Budget:" in explanation
    assert "required_route" in explanation


def test_cli_warning_only_success_and_invalid_task_exit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    route_manifest(
        tmp_path,
        required=[{"path": "missing.md", "category": "required"}],
    )

    assert task_context.main(["build", "feature", "--no-search"], root=tmp_path) == 0
    captured = capsys.readouterr()
    assert "Task context written:" in captured.out
    assert "warning:" in captured.err
    assert task_context.main(["build", "   ", "--no-search"], root=tmp_path) == 2


def test_cli_invalid_configuration_and_materialization_failure_exit_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route_manifest(tmp_path)
    manifest = tmp_path / "docs" / "agent" / "context-routes.json"
    manifest.write_text("not-json", encoding="utf-8")
    assert task_context.main(["explain", "feature", "--no-search"], root=tmp_path) == 2

    route_manifest(tmp_path)

    def fail_materialization(root: Path, result: engine.BuildResult) -> Path:
        raise engine.TaskContextError("materialization failed")

    monkeypatch.setattr(task_context, "materialize_bundle", fail_materialization)
    assert task_context.main(["build", "feature", "--no-search"], root=tmp_path) == 2


def test_cli_stdout_hashed_markdown_only_and_explain(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path / "required.md", "required\n")
    route_manifest(tmp_path, required=[{"path": "required.md", "category": "required"}])

    assert task_context.main(["build", "Feature Work", "--no-search", "--stdout"], root=tmp_path) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("# Task Context\n")
    cache = tmp_path / ".agent" / "context-cache" / "task-context"
    assert sorted(path.name for path in cache.iterdir()) == [
        f"{engine.task_hash('feature work')}.md", f"{engine.task_hash('feature work')}.read.md",
    ]
    assert "Compact reading view" in captured.out
    assert task_context.main(["explain", "Feature Work", "--no-search"], root=tmp_path) == 0
    assert "Route: primary" in capsys.readouterr().out


def test_make_targets_build_and_explain_context() -> None:
    make = shutil.which("make")
    if not make:
        pytest.skip("make is unavailable")
    task = "task context make integration fixture"
    destination = ROOT / ".agent" / "context-cache" / "task-context" / f"{engine.task_hash(task)}.md"
    try:
        built = subprocess.run(
            [make, "task-context", f"TASK={task}", "ROUTE=general"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        assert built.returncode == 0, built.stdout + built.stderr
        assert destination.exists()
        assert destination.name in built.stdout

        explained = subprocess.run(
            [make, "task-context-explain", f"TASK={task}", "ROUTE=general"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        assert explained.returncode == 0, explained.stdout + explained.stderr
        assert "Route: general" in explained.stdout
    finally:
        destination.unlink(missing_ok=True)
        destination.with_suffix(".read.md").unlink(missing_ok=True)


def test_golden_evaluation_mismatch_returns_one(tmp_path: Path) -> None:
    fixtures = json.loads((ROOT / "eval" / "context" / "golden_tasks.json").read_text(encoding="utf-8"))
    fixtures["cases"][0]["expected_docs"] = ["does/not/exist.md"]
    fixture_path = tmp_path / "mismatch.json"
    write(fixture_path, json.dumps(fixtures))

    assert run_task_context_eval.run(fixture_path, ROOT) == 1


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


def test_expansion_priority_and_same_path_document_budget(tmp_path: Path) -> None:
    for name in ("required", "explicit", "feature-optional", "search"):
        write(tmp_path / f"{name}.md", name + " fact\n")
    route_manifest(
        tmp_path, required=[{"path": "required.md", "category": "required"}],
        optional=[{"path": "feature-optional.md", "category": "optional"}], max_docs=2,
    )
    result = engine.build_task_context(
        "feature feature-optional.md", tmp_path,
        search_provider=lambda *args: engine.SearchOutcome("ok", [engine.SearchResult("search.md", 1, 1)]),
        expand_sources=[("required.md", 1, 1), ("explicit.md", 1, 1)], reason="Need explicit facts",
    )
    assert [source.path for source in result.selected] == ["required.md", "explicit.md"]
    assert "already included" in result.expansion_notes[0]
    assert {item.path for item in result.dropped if item.reason == "document_budget_exhausted"} == {
        "feature-optional.md", "search.md",
    }


def test_expansion_budget_preserves_required_excerpt_and_reports_truncation(tmp_path: Path) -> None:
    write(tmp_path / "guide.md", "## Required\nrequired fact\n## Extra\n" + "E" * 200)
    route_manifest(tmp_path, required=[{
        "path": "guide.md", "category": "guide", "sections": ["Required"],
    }], max_chars=100)
    required = engine.build_task_context("feature", tmp_path, use_search=False).selected[0].excerpt
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False,
        expand_sources=[("guide.md", 3, 4)], reason="Need extra details",
    )
    assert result.selected[0].excerpt.startswith(required)
    assert result.selected_chars <= 100
    assert result.selected[0].truncated
    assert "included with truncation" in result.expansion_notes[0]
    assert any("Truncated context" in warning for warning in result.warnings)


@pytest.mark.parametrize("budget,expected", [("docs", "document_budget_exhausted"), ("chars", "character_budget_exhausted")])
def test_rejected_expansion_explains_exhausted_budget(tmp_path: Path, budget: str, expected: str) -> None:
    write(tmp_path / "required.md", "R" * 60)
    write(tmp_path / "extra.md", "extra\n")
    route_manifest(
        tmp_path, required=[{"path": "required.md", "category": "required"}],
        max_docs=1 if budget == "docs" else 10, max_chars=60 if budget == "chars" else 40000,
    )
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False, expand_sources=[("extra.md", 1, 1)], reason="Need extra",
    )
    assert [item.excerpt for item in result.selected] == ["R" * 60]
    assert "rejected" in result.expansion_notes[0]
    assert expected in result.expansion_notes[0]


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


def test_expansion_redacts_reason_and_excerpt_in_both_renderers(tmp_path: Path) -> None:
    write(tmp_path / "safe.md", "token=source-value\nhttps://name:password@example.test/\n")
    route_manifest(tmp_path)
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False, expand_sources=[("safe.md", 1, 2)],
        reason="Resolve api_key=reason-value and https://name:secret@example.test/",
    )
    for rendered in (engine.render_markdown(result), engine.render_explanation(result)):
        assert "reason-value" not in rendered
        assert "name:secret" not in rendered
        assert "source-value" not in rendered
        assert "name:password" not in rendered
        assert "Reason: Resolve api_key=<REDACTED-SECRET>" in rendered
    assert result.selected[0].redactions == {"url_credentials": 1, "secret_assignment": 1}


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


def test_cli_expansion_requires_reason_and_accepts_repeated_ranges(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path / "extra.md", "one\ntwo\nthree\n")
    route_manifest(tmp_path)
    base = ["explain", "feature", "--no-search"]
    assert task_context.main(base + ["--expand-source", "extra.md", "1", "2"], root=tmp_path) == 2
    assert "requires a non-empty --reason" in capsys.readouterr().err
    assert task_context.main(base + ["--reason", "unused"], root=tmp_path) == 2
    assert task_context.main(base + ["--expand-source", "extra.md", "first", "2", "--reason", "fact"], root=tmp_path) == 2
    capsys.readouterr()
    assert task_context.main(base + [
        "--expand-source", "extra.md", "1", "2", "--expand-source", "extra.md", "2", "3",
        "--reason", "Missing details",
    ], root=tmp_path) == 0
    assert "`extra.md` lines 1-2, 2-3: included." in capsys.readouterr().out
    assert not (tmp_path / ".agent/context-cache").exists()


def test_expansion_partial_section_fallback_and_windows_lines(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_bytes(b"Intro\r\n## A\r\nA fact\r\n\r\n## B\r\nB fact\r\n")
    route_manifest(tmp_path, required=[{"path": "guide.md", "category": "guide", "sections": ["A"]}])
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False,
        expand_sources=[("guide.md", 1, 6)], reason="Need rest of guide",
    )
    assert result.selected[0].excerpt.count("A fact") == 1
    assert result.selected[0].excerpt.count("B fact") == 1
    assert result.selected[0].excerpt.startswith("## A\r\nA fact")
    route_manifest(tmp_path, required=[{"path": "guide.md", "category": "guide", "sections": ["Missing"]}])
    fallback = engine.build_task_context(
        "feature", tmp_path, use_search=False, expand_sources=[("guide.md", 1, 6)], reason="Need guide",
    )
    assert "already included" in fallback.expansion_notes[0]


def test_expansion_distinguishes_heading_named_all_from_full_file(tmp_path: Path) -> None:
    write(tmp_path / "guide.md", "## all\nall section\n## Other\nother section\n")
    route_manifest(tmp_path, required=[{"path": "guide.md", "category": "guide", "sections": ["all"]}])
    result = engine.build_task_context(
        "feature", tmp_path, use_search=False, expand_sources=[("guide.md", 3, 4)], reason="Need other section",
    )
    assert result.selected[0].excerpt.count("all section") == 1
    assert "other section" in result.selected[0].excerpt


def test_truncated_required_source_does_not_claim_omitted_expansion_is_included(tmp_path: Path) -> None:
    write(tmp_path / "guide.md", "intro\n" * 26 + "requested last fact\n")
    route_manifest(tmp_path, required=[{"path": "guide.md", "category": "guide"}], max_chars=70)
    result = engine.build_task_context("feature", tmp_path, use_search=False,
        expand_sources=[("guide.md", 27, 27)], reason="Need final fact")
    assert "requested last fact" not in result.selected[0].excerpt
    assert "already included" not in result.expansion_notes[0]
    assert "character_budget_exhausted" in result.expansion_notes[0]
    assert result.selected_chars <= 70


@pytest.mark.parametrize("exists", [False, True])
def test_expansion_path_is_redacted_in_all_output(tmp_path: Path, capsys, exists: bool) -> None:
    filename = "api_key=FAKE-ONLY-REVIEW"
    route_manifest(tmp_path)
    if exists:
        write(tmp_path / filename, "ordinary text\n")
    result = engine.build_task_context("feature", tmp_path, use_search=False,
        expand_sources=[(filename, 1, 1)], reason="Need context")
    for output in (engine.render_markdown(result), engine.render_explanation(result), "\n".join(result.warnings)):
        assert "FAKE-ONLY-REVIEW" not in output
    assert task_context.main(["build", "feature", "--no-search", "--expand-source", filename, "1", "1", "--reason", "Need context"], root=tmp_path) == 0
    captured = capsys.readouterr()
    assert "FAKE-ONLY-REVIEW" not in captured.out + captured.err


@pytest.mark.parametrize("destination", ["secrets/source.txt", ".agent/context-cache/source.txt"])
def test_expansion_rechecks_resolved_alias_against_secret_and_exclusion_policy(tmp_path: Path, monkeypatch, destination: str) -> None:
    route_manifest(tmp_path)
    write(tmp_path / destination, "FAKE-CREDENTIAL-MUST-NOT-BE-READ\n")
    alias = tmp_path / "public/source.txt"
    original = Path.resolve
    # Portable simulation of filesystem alias resolution; does not require Windows symlink privilege.
    def resolve(path, *args, **kwargs):
        if path == alias:
            return original(tmp_path / destination)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", resolve)
    result = engine.build_task_context("feature", tmp_path, use_search=False,
        expand_sources=[("public/source.txt", 1, 1)], reason="Read alias")
    assert not result.selected
    assert "FAKE-CREDENTIAL-MUST-NOT-BE-READ" not in engine.render_markdown(result)
    assert "rejected" in result.expansion_notes[0]


def test_login_regression_omits_unrelated_agent_evaluation_tests() -> None:
    result = engine.build_task_context("Fix a failing login regression", ROOT, use_search=False)
    selected = {source.path for source in result.selected}
    assert "tests/agent/test_decision_advice.py" not in selected
    assert "tests/agent/test_behavior_eval.py" not in selected
    assert {source.origin for source in result.selected} == {"routed-required"}


@pytest.mark.parametrize("task,path,content", [
    ("feature fix payments module", "tests/test_payments.py", "unrelated content\n"),
    ("feature inspect calculate_total()", "helpers.py", "def calculate_total():\n    return 42\n"),
    ("feature fix _normalize_expansions", "helpers.py", "def _normalize_expansions():\n    return []\n"),
    ("feature inspect f()", "helpers.py", "def f():\n    return 42\n"),
    ("feature inspect test_decision_advice.py", "tests/test_decision_advice.py", "unrelated content\n"),
])
def test_concrete_module_path_and_symbol_optional_matches_survive(tmp_path: Path, task: str, path: str, content: str) -> None:
    write(tmp_path / path, content)
    route_manifest(tmp_path, optional=[{"path": path, "category": "test"}])
    result = engine.build_task_context(task, tmp_path, use_search=False)
    assert [source.path for source in result.selected] == [path]


def test_optional_incidental_word_cannot_select_a_large_file(tmp_path: Path) -> None:
    write(tmp_path / "unrelated.py", "# login mentioned once\n" + "other content\n" * 1000)
    route_manifest(tmp_path, optional=[{"path": "unrelated.py", "category": "test"}])
    result = engine.build_task_context("feature fix login regression", tmp_path, use_search=False)
    assert not result.selected
    assert result.dropped[0].reason == "no_task_relevance"


def test_large_optional_source_uses_relevant_windows_and_whole_file_hash(tmp_path: Path) -> None:
    source = "# early unrelated material\n" * 400 + "def calculate_total():\n    return 42\n" + "# later unrelated\n" * 400
    write(tmp_path / "helpers.py", source)
    route_manifest(tmp_path, optional=[{"path": "helpers.py", "category": "test"}])
    result = engine.build_task_context("feature fix calculate_total", tmp_path, use_search=False)
    selected = result.selected[0]
    assert "def calculate_total" in selected.excerpt
    assert selected.char_count <= engine.OPTIONAL_EXCERPT_CHARS
    assert len(selected.excerpt.splitlines()) <= engine.OPTIONAL_EXCERPT_LINES
    assert selected.source_hash == hashlib.sha256((tmp_path / "helpers.py").read_bytes()).hexdigest()
    assert selected.line_ranges[0][0] > 1
    assert any("remaining content omitted" in warning for warning in result.warnings)


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


def test_compact_aggregates_drops_without_hiding_warnings_or_gaps(tmp_path: Path) -> None:
    route_manifest(tmp_path, required=[{"path": "missing.md", "category": "required"}])
    result = engine.build_task_context("feature", tmp_path, use_search=False)
    result.dropped.extend(engine.DroppedSource(f"unrelated-{index}.md", "routed-optional", "no_task_relevance") for index in range(500))
    compact = engine.render_compact_markdown(result)
    assert "501 dropped candidates" in compact
    assert "no_task_relevance=500" in compact
    assert "unrelated-499.md" not in compact
    assert all(warning in compact for warning in result.warnings)
    assert all(gap in compact for gap in result.gaps)
    assert len(compact) < 2000
    assert "unrelated-499.md" in engine.render_markdown(result)


def test_compact_overflow_fails_explicitly_retaining_full_audit(tmp_path: Path, capsys) -> None:
    write(tmp_path / "required.md", "R" * 300)
    route_manifest(tmp_path, required=[{"path": "required.md", "category": "required"}], max_chars=300)
    cache = tmp_path / ".agent/context-cache/task-context"
    reading = cache / f"{engine.task_hash('feature')}.read.md"
    write(reading, "obsolete reading artifact")
    assert task_context.main(["build", "feature", "--no-search"], root=tmp_path) == 2
    assert "Required content was not silently omitted" in capsys.readouterr().err
    assert not reading.exists()
    audit = cache / f"{engine.task_hash('feature')}.md"
    assert audit.exists() and "R" * 300 in audit.read_text(encoding="utf-8")
    assert task_context.main(["build", "feature", "--no-search", "--view", "full", "--stdout"], root=tmp_path) == 0
    assert "Full audit view" in capsys.readouterr().out


def test_compact_memory_projection_uses_exact_hashed_snapshot(tmp_path: Path) -> None:
    entry = {"id": "lesson", "path": ".agent/memory/lesson.md", "type": "semantic", "scope": "project",
             "summary": "Current useful lesson", "keywords": [], "confidence": "high", "last_verified": "2026-09-23",
             "source_task": ".agent/task.md", "evidence": [{"path": "source.md", "sha256": "0" * 64}]}
    text = json.dumps({"version": 1, "memories": [entry]})
    write(tmp_path / ".agent/memory/index.json", text)
    write(tmp_path / ".agent/memory/lesson.md", "lesson")
    write(tmp_path / "source.md", "changed source")
    route_manifest(tmp_path, required=[{"path": ".agent/memory/index.json", "category": "memory-index"}])
    result = engine.build_task_context("feature memory", tmp_path, use_search=False)
    write(tmp_path / ".agent/memory/index.json", "invalid newer index")
    compact = engine.render_compact_markdown(result)
    assert "Current useful lesson" in compact and "needs-reverification" in compact
    assert "0" * 64 not in compact
    assert "Compact memory projection" in compact
    assert result.selected[0].source_hash == hashlib.sha256(text.encode()).hexdigest()
    assert "0" * 64 in engine.render_markdown(result)
    assert "invalid newer index" not in compact


def test_compact_preserves_explicit_expansion_and_redaction(tmp_path: Path) -> None:
    write(tmp_path / "extra.md", "token=source-secret\nexplicit fact\n")
    route_manifest(tmp_path)
    result = engine.build_task_context("feature", tmp_path, use_search=False,
        expand_sources=[("extra.md", 1, 2)], reason="Resolve token=reason-secret")
    compact = engine.render_compact_markdown(result)
    assert "explicit fact" in compact and "explicit_expansion" in compact
    assert "source-secret" not in compact and "reason-secret" not in compact
    assert all(warning in compact for warning in result.warnings)


def test_large_optional_line_redacts_before_clipping(tmp_path: Path) -> None:
    password = "FAKE-ONLY-CREDENTIAL-" * 400
    write(tmp_path / "payments.md", f"https://name:{password}@example.test/\n")
    route_manifest(tmp_path, optional=[{"path": "payments.md", "category": "optional"}])
    result = engine.build_task_context("feature payments", tmp_path, use_search=False)
    assert "FAKE-ONLY-CREDENTIAL" not in engine.render_compact_markdown(result)
    assert "FAKE-ONLY-CREDENTIAL" not in engine.render_markdown(result)
    assert result.selected[0].redactions == {"url_credentials": 1}


def test_full_only_rebuild_invalidates_old_compact_companion(tmp_path: Path) -> None:
    write(tmp_path / "required.md", "old source")
    route_manifest(tmp_path, required=[{"path": "required.md", "category": "required"}])
    assert task_context.main(["build", "feature", "--no-search"], root=tmp_path) == 0
    reading = tmp_path / ".agent/context-cache/task-context" / f"{engine.task_hash('feature')}.read.md"
    assert reading.exists()
    write(tmp_path / "required.md", "new source")
    assert task_context.main(["build", "feature", "--no-search", "--view", "full"], root=tmp_path) == 0
    assert not reading.exists()
    assert "new source" in reading.with_name(f"{engine.task_hash('feature')}.md").read_text(encoding="utf-8")
