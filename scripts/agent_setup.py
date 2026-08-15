import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def detect_stack() -> list[str]:
    stack = []
    if exists("pyproject.toml") or exists("requirements.txt"):
        stack.append("python")
    if exists("package.json"):
        stack.append("node")
    if exists("go.mod"):
        stack.append("go")
    if exists("Cargo.toml"):
        stack.append("rust")
    return stack or ["unknown"]


def package_scripts() -> dict[str, str]:
    path = ROOT / "package.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("scripts", {})


def detect_commands() -> dict[str, str]:
    scripts = package_scripts()
    commands = {}
    for name in ["test", "lint", "typecheck", "dev"]:
        if name in scripts:
            commands[name] = f"npm run {name}"

    makefile = ROOT / "Makefile"
    if makefile.exists():
        make_text = makefile.read_text(encoding="utf-8")
        for name in [
            "agent-tools-install",
            "agent-tools-check",
            "agent-kit-check",
            "test",
            "test-unit",
            "test-integration",
            "lint",
            "typecheck",
            "dev",
            "code-search",
            "repomix",
            "ast-grep",
            "rtk-gain",
            "git-status",
            "git-diff",
            "test-unit-compact",
            "lint-compact",
            "typecheck-compact",
            "understand",
            "understand-search",
            "understand-dashboard",
            "retrieval-eval",
            "validate-agent-assets",
            "codex-guardrails-enable",
            "codex-runtime-check",
            "skill-routing-eval",
            "task-context",
            "task-context-explain",
            "task-context-eval",
        ]:
            if f"{name}:" in make_text:
                commands[name] = f"make {name}"

    if exists("pyproject.toml") and "test" not in commands:
        commands["test"] = "pytest"
    return commands


def write_commands(commands: dict[str, str]) -> None:
    lines = ["# Commands", "", "Detected project commands.", ""]
    for name, command in sorted(commands.items()):
        lines.append(f"- {name}: `{command}`")
    if not commands:
        lines.append("- TODO: add install, test, lint, typecheck, and dev commands.")
    lines.extend(
        [
            "",
            "Agent tool bootstrap:",
            "- agent-tools-install: `make agent-tools-install`",
            "- agent-tools-check: `make agent-tools-check`",
            "- no-make install: `python scripts/bootstrap_agent_tools.py`",
            "- no-make check: `python scripts/bootstrap_agent_tools.py --check`",
            "",
            "Source understanding helpers:",
            "- code-search: `make code-search QUERY=\"source understanding\" CONTENT=all`",
            "- ast-grep: `make ast-grep PATTERN=\"def $NAME($$$ARGS): $$$BODY\" LANG=python`",
            "- repomix: `make repomix`",
            "",
            "Task context compiler:",
            "- build: `make task-context TASK=\"describe the task\"`",
            "- explain: `make task-context-explain TASK=\"describe the task\"`",
            "- evaluate: `make task-context-eval`",
            "",
            "Optional compact-output helpers:",
            "- rtk-gain: `make rtk-gain`",
            "- git-status: `make git-status`",
            "- git-diff: `make git-diff`",
            "- test-unit-compact: `make test-unit-compact`",
            "- lint-compact: `make lint-compact`",
            "- typecheck-compact: `make typecheck-compact`",
            "",
            "Memory helpers:",
            "- extract-task-memory: `make extract-task-memory TASK=.agent/tasks/<task>.md`",
            "- validate-memory-links: `make validate-memory-links`",
            "- audit-memory-staleness: `make audit-memory-staleness`",
            "- audit-memory: `make audit-memory`",
            "",
            "Codex customization:",
            "- validate-agent-assets: `make validate-agent-assets`",
            "- agent-kit-check: `make agent-kit-check`",
            "- codex-guardrails-enable: `make codex-guardrails-enable`",
            "- codex-runtime-check: `make codex-runtime-check`",
            "- skill-routing-eval: `make skill-routing-eval`",
        ]
    )
    (ROOT / "docs" / "agent" / "COMMANDS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_task_readme() -> None:
    path = ROOT / ".agent" / "tasks" / "README.md"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Task Logs\n\n"
        "Use one markdown file per multi-step task. Include the goal, docs read, files inspected, "
        "commands run, compressed-output usage, raw reruns, verification, memory extraction notes, "
        "and follow-up risk.\n",
        encoding="utf-8",
    )


def ensure_memory_scaffold() -> None:
    memory_root = ROOT / ".agent" / "memory"
    files = {
        "README.md": (
            "# Agent Memory\n\n"
            "Use this folder for semantic and procedural memory. Memory is guidance, not truth; "
            "verify it against current files before editing.\n"
        ),
        "index.json": '{\n  "version": 1,\n  "memories": []\n}\n',
        "semantic/project-facts.md": "# Memory: Project Facts\n\nTODO: add promoted semantic memory.\n",
        "semantic/conventions.md": "# Memory: Project Conventions\n\nTODO: add promoted semantic memory.\n",
        "semantic/decisions.md": "# Memory: Template Decisions\n\nTODO: add promoted semantic memory.\n",
        "procedural/debugging-playbooks.md": "# Memory: Debugging Playbooks\n\nTODO: add promoted procedural memory.\n",
        "procedural/testing-playbooks.md": "# Memory: Testing Playbooks\n\nTODO: add promoted procedural memory.\n",
        "procedural/refactor-playbooks.md": "# Memory: Refactor Playbooks\n\nTODO: add promoted procedural memory.\n",
        "candidates/README.md": (
            "# Candidate Memory\n\n"
            "Generated candidates require manual review before promotion.\n"
        ),
    }
    for relative, text in files.items():
        path = memory_root / relative
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def ensure_agent_entrypoints(stack: list[str], commands: dict[str, str]) -> None:
    summary = ", ".join(stack)
    command_lines = "\n".join(f"- {name}: `{command}`" for name, command in sorted(commands.items()))
    if not command_lines:
        command_lines = "- TODO: confirm project commands."

    for filename in ["AGENTS.md", "CLAUDE.md"]:
        path = ROOT / filename
        if path.exists():
            continue
        path.write_text(
            f"# {filename}\n\n"
            f"Project stack: {summary}.\n\n"
            "Start by reading `docs/agent/INDEX.md`, then build and inspect task context with "
            "`python scripts/task_context.py build \"<task>\"` before non-trivial work.\n\n"
            "Prefer compressed output for noisy commands when RTK is available, and rerun raw output only "
            "when failures are unclear.\n\n"
            "## Commands\n"
            f"{command_lines}\n",
            encoding="utf-8",
        )


def run_script(relative: str) -> int:
    result = subprocess.run([sys.executable, relative], cwd=ROOT, check=False)
    return result.returncode


def run_task_context_smoke() -> int:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/task_context.py",
            "build",
            "validate the installed agent setup",
            "--route",
            "agent-setup",
            "--no-search",
        ],
        cwd=ROOT,
        check=False,
    )
    return result.returncode


def main() -> None:
    stack = detect_stack()
    commands = detect_commands()
    write_commands(commands)
    ensure_task_readme()
    ensure_memory_scaffold()
    ensure_agent_entrypoints(stack, commands)

    failures = []
    scripts = ["scripts/validate_agent_assets.py"]
    if exists("src"):
        scripts[0:0] = [
            "scripts/generate_codemap.py",
            "scripts/update_module_cards.py",
        ]
    for script in scripts:
        if run_script(script) != 0:
            failures.append(script)
    if run_task_context_smoke() != 0:
        failures.append("task-context smoke check")

    print(f"Detected stack: {', '.join(stack)}")
    print(f"Detected commands: {', '.join(sorted(commands)) or 'none'}")
    if failures:
        print("Validation failures:")
        for script in failures:
            print(f"- {script}")
        raise SystemExit(1)
    print("Agent setup complete.")


if __name__ == "__main__":
    main()
