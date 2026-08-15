import json
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

    result = engine.build_task_context("feature work", tmp_path, search_provider=search)

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
    assert [path.name for path in cache.iterdir()] == [f"{engine.task_hash('feature work')}.md"]
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


def test_golden_evaluation_mismatch_returns_one(tmp_path: Path) -> None:
    fixtures = json.loads((ROOT / "eval" / "context" / "golden_tasks.json").read_text(encoding="utf-8"))
    fixtures["cases"][0]["expected_docs"] = ["does/not/exist.md"]
    fixture_path = tmp_path / "mismatch.json"
    write(fixture_path, json.dumps(fixtures))

    assert run_task_context_eval.run(fixture_path, ROOT) == 1
