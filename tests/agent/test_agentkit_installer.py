import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agentkit_installer import BEGIN, END, check, exclusion_patterns, install, iter_manifest_paths


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_source(root: Path) -> None:
    manifest = {
        "schema_version": 2,
        "version": "0.5.0",
        "skills": [],
        "included_harness_files": ["kit/"],
        "merge_files": ["AGENTS.md"],
        "copy_if_missing_files": [".agent/memory.md"],
        "project_local_files": [],
        "excluded_files": [],
        "symlinks": [],
    }
    write(root / "agentkit-manifest.json", json.dumps(manifest))
    write(root / "kit" / "current.txt", "current\n")
    write(root / "AGENTS.md", "# Managed instructions\n")
    write(root / ".agent" / "memory.md", "starter memory\n")


def test_fresh_install_and_reinstall_are_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)
    write(target / "CLAUDE.md", "# Unmanaged project instructions\n")

    install("install", source, target)
    first_state = (target / ".agentkit-installed-files").read_text(encoding="utf-8")
    install("update", source, target)

    assert (target / "kit" / "current.txt").read_text(encoding="utf-8") == "current\n"
    assert (target / ".agentkit-installed-files").read_text(encoding="utf-8") == first_state
    assert (target / "AGENTS.md").read_text(encoding="utf-8").count("<!-- agentkit:begin -->") == 1
    assert (target / "CLAUDE.md").read_text(encoding="utf-8") == "# Unmanaged project instructions\n"
    assert "CLAUDE.md" not in first_state.splitlines()


def test_project_ownership_is_rooted_but_runtime_exclusions_remain_recursive(tmp_path: Path) -> None:
    for path in ("src/user.py", "eval/fixtures/initial/src/sample.py",
                 "eval/fixtures/initial/docs/specs/contract.md",
                 "eval/fixtures/initial/src/__pycache__/sample.pyc"):
        write(tmp_path / path, "content")
    manifest = {"project_local_files": ["src/", "docs/specs/"],
                "excluded_files": ["__pycache__/", "*.pyc"]}
    selected = {p.relative_to(tmp_path).as_posix() for p in
                iter_manifest_paths(tmp_path, ["src/", "eval/"], exclusion_patterns(manifest))}
    assert selected == {"eval/fixtures/initial/src/sample.py", "eval/fixtures/initial/docs/specs/contract.md"}


def test_update_backs_up_and_prunes_only_recorded_obsolete_files(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)
    write(target / "kit" / "obsolete.txt", "old managed content\n")
    write(target / "kit" / "user.txt", "user content\n")
    write(target / ".agent" / "memory.md", "user memory\n")
    write(target / "CLAUDE.md", "# User instructions replaced the old kit block\n")
    write(
        target / ".agentkit-installed-files",
        "kit/obsolete.txt\n.agent/memory.md\nAGENTS.md\nCLAUDE.md\n",
    )

    install("update", source, target)

    assert not (target / "kit" / "obsolete.txt").exists()
    assert (target / "kit" / "user.txt").read_text(encoding="utf-8") == "user content\n"
    assert (target / ".agent" / "memory.md").read_text(encoding="utf-8") == "user memory\n"
    backups = list((target / ".agentkit" / "backups").glob("*/kit/obsolete.txt"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "old managed content\n"
    assert (target / "CLAUDE.md").read_text(encoding="utf-8") == "# User instructions replaced the old kit block\n"
    assert "CLAUDE.md" not in (target / ".agentkit-installed-files").read_text(encoding="utf-8").splitlines()
    assert "left unmarked or ambiguously marked legacy CLAUDE.md untouched" in capsys.readouterr().out


def test_update_removes_legacy_kit_block_but_preserves_user_bytes(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)
    before = "# Project instructions\r\nKeep caf\u00e9 names.\r\n\r\n"
    after = "\r\n\r\n# User footer\r\nKeep release notes.\r\n"
    original = (before + BEGIN + "\r\n# Old kit instructions\r\n" + END + after).encode("utf-8")
    write(target / ".agentkit-installed-files", "CLAUDE.md\n")
    (target / "CLAUDE.md").write_bytes(original)

    install("update", source, target)

    assert (target / "CLAUDE.md").read_bytes() == (before + after).encode("utf-8")
    backups = list((target / ".agentkit/backups").glob("*/CLAUDE.md"))
    assert len(backups) == 1 and backups[0].read_bytes() == original
    assert "CLAUDE.md" not in (target / ".agentkit-installed-files").read_text(encoding="utf-8").splitlines()
    assert "Consolidate user instructions into AGENTS.md and verify native AGENTS.md loading" in capsys.readouterr().out


def test_update_leaves_legacy_claude_symlink_and_target_untouched(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)
    original = f"{BEGIN}\n# Foreign instructions\n{END}\n"
    foreign = tmp_path / "foreign.md"
    write(foreign, original)
    write(target / ".agentkit-installed-files", "CLAUDE.md\n")
    legacy = target / "CLAUDE.md"
    try:
        legacy.symlink_to(foreign)
    except OSError:
        pytest.skip("Symlink creation is unavailable on this platform.")

    install("update", source, target)

    assert legacy.is_symlink()
    assert foreign.read_text(encoding="utf-8") == original
    assert not list((target / ".agentkit/backups").glob("*/CLAUDE.md"))
    assert "CLAUDE.md" not in (target / ".agentkit-installed-files").read_text(encoding="utf-8").splitlines()
    assert "left legacy CLAUDE.md untouched because it is not a regular file" in capsys.readouterr().out


def test_real_manifest_install_provides_declared_skills_and_working_setup(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "installed-project"

    install("install", source, target)

    manifest = json.loads((source / "agentkit-manifest.json").read_text(encoding="utf-8"))
    skills = {path.parent.name for path in (target / ".agents" / "skills").glob("*/SKILL.md")}
    assert skills == {entry["name"] for entry in manifest["skills"]}
    assert {"task-context", "test-scope"} <= skills
    assert (target / "AGENTS.md").is_file()
    assert not (target / "CLAUDE.md").exists()
    assert (target / "scripts" / "task_context.py").is_file()
    assert (target / "docs" / "agent" / "context-routes.json").is_file()
    assert (target / "eval" / "context" / "golden_tasks.json").is_file()
    assert (target / "docs" / "adr" / "0004-task-context-compiler.md").is_file()
    assert (target / "docs" / "adr" / "0005-measurable-reliability.md").is_file()
    assert (target / "scripts" / "decision_advice.py").is_file()
    assert (target / "scripts" / "memory_lookup.py").is_file()
    assert (target / "eval" / "behavior" / "run_behavior_eval.py").is_file()
    assert (target / "eval" / "advice" / "cases.json").is_file()
    assert not (target / ".codex" / "hooks.json").exists()
    assert not (target / ".codex" / "rules" / "default.rules").exists()
    assert not list(target.rglob("__pycache__"))
    assert not list(target.rglob("*.pyc"))
    assert check(source, target) == 0

    setup = subprocess.run(
        [sys.executable, "scripts/agent_setup.py"],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert setup.returncode == 0, setup.stdout + setup.stderr
    assert list((target / ".agent" / "context-cache" / "task-context").glob("*.md"))
    assert list((target / ".agent" / "context-cache" / "task-context").glob("*.read.md"))
    assert not (target / "CLAUDE.md").exists()

    legacy = f"{BEGIN}\n# Old kit instructions\n{END}\n"
    write(target / "CLAUDE.md", legacy)
    state = target / ".agentkit-installed-files"
    state.write_text(state.read_text(encoding="utf-8") + "CLAUDE.md\n", encoding="utf-8")
    install("update", source, target)

    assert not (target / "CLAUDE.md").exists()
    assert "CLAUDE.md" not in state.read_text(encoding="utf-8").splitlines()
    backups = list((target / ".agentkit/backups").glob("*/CLAUDE.md"))
    assert len(backups) == 1 and backups[0].read_text(encoding="utf-8") == legacy
