import json
from pathlib import Path

from scripts.validate_agent_assets import (
    ValidationReport,
    discover_instruction_chain,
    validate_instructions,
    validate_manifest_and_skills,
    validate_task_context_routes,
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_instruction_chain_keeps_ancestor_and_prefers_same_level_override(tmp_path: Path) -> None:
    write(tmp_path / "AGENTS.md", "# Root\n")
    write(tmp_path / "service" / "AGENTS.md", "# Service base\n")
    write(tmp_path / "service" / "AGENTS.override.md", "# Service override\n")

    chain = discover_instruction_chain(tmp_path, tmp_path / "service")

    assert [path.relative_to(tmp_path).as_posix() for path in chain] == [
        "AGENTS.md",
        "service/AGENTS.override.md",
    ]


def test_instruction_budget_counts_utf8_bytes(tmp_path: Path) -> None:
    write(tmp_path / "AGENTS.md", "# Root\n")
    write(tmp_path / "module" / "AGENTS.md", "é" * 3000)
    report = ValidationReport()

    validate_instructions(tmp_path, report)

    assert any("exceeds its 4096-byte limit" in error for error in report.errors)


def test_task_context_routes_report_index_drift(tmp_path: Path) -> None:
    write(tmp_path / "docs" / "agent" / "INDEX.md", "## Different Heading\n")
    manifest = {
        "schema_version": 1,
        "index_path": "docs/agent/INDEX.md",
        "defaults": {
            "max_docs": 10,
            "max_chars": 40000,
            "search_content": "all",
            "search_limit": 5,
            "selection_order": [
                "routed-required",
                "routed-optional",
                "advisory-search",
            ],
        },
        "exclude_globs": [],
        "routes": [
            {
                "id": "general",
                "index_heading": "General Route",
                "triggers": [],
                "required": [],
                "optional": [],
            }
        ],
    }
    write(
        tmp_path / "docs" / "agent" / "context-routes.json",
        json.dumps(manifest),
    )
    report = ValidationReport()

    validate_task_context_routes(tmp_path, report)

    assert any("## General Route" in error for error in report.errors)


def test_ci_delegation_requires_full_suite_in_test_workflow(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    for relative in ("agentkit-manifest.json", ".github/workflows/agent-doc-check.yml", ".github/workflows/test.yml"):
        write(tmp_path / relative, (source / relative).read_text(encoding="utf-8"))
    report = ValidationReport()
    validate_manifest_and_skills(tmp_path, report)
    assert not any("CI must" in error for error in report.errors)

    # An application-only subset would silently lose the delegated agent tests.
    workflow = tmp_path / ".github/workflows/test.yml"
    write(workflow, "steps:\n  - run: python -m pytest tests/unit -q\n")
    report = ValidationReport()
    validate_manifest_and_skills(tmp_path, report)
    assert any("Test CI must run the full" in error for error in report.errors)
