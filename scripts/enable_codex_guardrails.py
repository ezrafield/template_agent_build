import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
HOOK_EVENTS = {
    "SESSION_START": "session-start",
    "USER_PROMPT": "user-prompt-submit",
    "STOP": "stop",
}
LOCAL_EXCLUDES = ["/.codex/hooks.json", "/.codex/rules/default.rules"]


def command_for(handler: Path, event: str, windows: bool) -> str:
    arguments = [sys.executable, str(handler), event]
    return subprocess.list2cmdline(arguments) if windows else shlex.join(arguments)


def render_hook_template(template: dict, handler: Path) -> dict:
    replacements: dict[str, str] = {}
    for placeholder, event in HOOK_EVENTS.items():
        replacements[f"{{{{{placeholder}_COMMAND}}}}"] = command_for(handler, event, windows=False)
        replacements[f"{{{{{placeholder}_COMMAND_WINDOWS}}}}"] = command_for(handler, event, windows=True)

    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, str):
            return replacements.get(value, value)
        return value

    return replace(template)


def add_local_git_excludes(root: Path) -> bool:
    git_dir_result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if git_dir_result.returncode != 0:
        return False
    git_dir = Path(git_dir_result.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    exclude_path = git_dir / "info" / "exclude"
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    existing_lines = set(existing.splitlines())
    additions = [entry for entry in LOCAL_EXCLUDES if entry not in existing_lines]
    if additions:
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        exclude_path.write_text(existing + prefix + "\n".join(additions) + "\n", encoding="utf-8")
    return True


def enable(root: Path) -> tuple[Path, Path]:
    root = root.resolve()
    template_root = root / ".codex" / "templates"
    hooks_template = template_root / "hooks.json"
    rules_template = template_root / "default.rules"
    hooks_target = root / ".codex" / "hooks.json"
    rules_target = root / ".codex" / "rules" / "default.rules"
    handler = root / "scripts" / "run_agent_hook.py"

    missing = [path for path in (hooks_template, rules_template, handler) if not path.is_file()]
    if missing:
        raise RuntimeError("Missing guardrail assets: " + ", ".join(str(path) for path in missing))
    existing = [path for path in (hooks_target, rules_target) if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite active guardrails: " + ", ".join(str(path) for path in existing)
        )

    template = json.loads(hooks_template.read_text(encoding="utf-8"))
    rendered = render_hook_template(template, handler)
    hooks_target.parent.mkdir(parents=True, exist_ok=True)
    rules_target.parent.mkdir(parents=True, exist_ok=True)
    hooks_target.write_text(json.dumps(rendered, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(rules_template, rules_target)
    add_local_git_excludes(root)
    return hooks_target, rules_target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enable machine-local Codex guardrails.")
    parser.add_argument("--target", default=str(DEFAULT_ROOT), help="Repository root to configure.")
    args = parser.parse_args(argv)
    try:
        hooks, rules = enable(Path(args.target))
    except (FileExistsError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Guardrail enablement failed: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {hooks}")
    print(f"Generated {rules}")
    print("Restart Codex, open /hooks, review the definitions, and trust them explicitly.")
    print("Run make codex-runtime-check before relying on the command rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
