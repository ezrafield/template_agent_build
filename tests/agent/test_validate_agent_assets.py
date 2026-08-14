from pathlib import Path

from scripts.validate_agent_assets import (
    ValidationReport,
    discover_instruction_chain,
    parse_skill_frontmatter,
    validate_instructions,
    validate_plan_system,
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


def test_instruction_chain_uses_configured_fallback(tmp_path: Path) -> None:
    write(tmp_path / "AGENTS.md", "# Root\n")
    write(tmp_path / "module" / "TEAM_GUIDE.md", "# Module\n")
    write(
        tmp_path / ".codex" / "config.toml",
        'project_doc_fallback_filenames = ["TEAM_GUIDE.md"]\n',
    )

    chain = discover_instruction_chain(tmp_path, tmp_path / "module")

    assert chain[-1].name == "TEAM_GUIDE.md"


def test_instruction_budget_counts_utf8_bytes(tmp_path: Path) -> None:
    write(tmp_path / "AGENTS.md", "# Root\n")
    write(tmp_path / "module" / "AGENTS.md", "é" * 3000)
    report = ValidationReport()

    validate_instructions(tmp_path, report)

    assert any("exceeds its 4096-byte limit" in error for error in report.errors)


def test_parse_skill_frontmatter_accepts_only_simple_metadata(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    write(
        skill,
        "---\nname: example-skill\ndescription: Use for an example workflow.\n---\n\n# Workflow\n",
    )

    metadata, body = parse_skill_frontmatter(skill)

    assert metadata == {"name": "example-skill", "description": "Use for an example workflow."}
    assert "# Workflow" in body


def test_plan_system_reports_learning_section_missing_from_record(tmp_path: Path) -> None:
    headings = [
        "Metadata",
        "Goal",
        "Why This Strategy",
        "Scope",
        "Success Signals",
        "Risks And Assumptions",
        "Outcome And Evidence",
        "Reflection",
    ]
    complete = "# Plan\n\n" + "\n\n".join(f"## {heading}" for heading in headings) + "\n"
    incomplete = complete.replace("\n\n## Reflection\n", "\n")
    for name in ("active", "backlog", "completed", "reports"):
        (tmp_path / ".agent" / "plans" / name).mkdir(parents=True, exist_ok=True)
    write(tmp_path / ".agent" / "plans" / "template.md", complete)
    write(
        tmp_path / ".agent" / "plans" / "active" / "2026-08-07-example.md",
        incomplete,
    )
    write(tmp_path / "AGENTS.md", "$plan-evolution .agent/plans/\n")
    write(tmp_path / "CLAUDE.md", ".agent/plans/\n")
    report = ValidationReport()

    validate_plan_system(tmp_path, report)

    assert any(
        ".agent/plans/active/2026-08-07-example.md is missing required heading ## Reflection."
        in error
        for error in report.errors
    )
