import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ASSET_PREFIXES = (
    ".agents/",
    ".claude/",
    ".codex/",
    ".github/workflows/agent-doc-check.yml",
    ".agent/memory/",
    "docs/agent/",
    "eval/agent/",
    "eval/rules/",
    "eval/skills/",
    "scripts/",
)
AGENT_ASSET_FILES = {
    "AGENTS.md",
    "AGENTS.override.md",
    "AGENTS.override.md.example",
    "CLAUDE.md",
    "Makefile",
    "package.json",
    "agentkit-manifest.json",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    re.compile(r"\bsk-(?:proj|svcacct)-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{48}\b"),
)


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Hook input must be a JSON object.")
    return value


def emit(value: dict) -> None:
    print(json.dumps(value, separators=(",", ":")))


def required_commands(root: Path) -> list[str]:
    manifest_path = root / "agentkit-manifest.json"
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    runtime = manifest.get("runtime", {})
    values = runtime.get("required_commands", []) if isinstance(runtime, dict) else []
    return [value for value in values if isinstance(value, str)]


def handle_session_start(root: Path) -> int:
    missing_commands = [
        command
        for command in required_commands(root)
        if not (command == "python" and sys.executable) and not shutil.which(command)
    ]
    missing_assets = [
        path
        for path in ("AGENTS.md", "docs/agent/INDEX.md", "agentkit-manifest.json")
        if not (root / path).is_file()
    ]
    if missing_commands or missing_assets:
        parts = []
        if missing_commands:
            parts.append("missing commands: " + ", ".join(sorted(missing_commands)))
        if missing_assets:
            parts.append("missing assets: " + ", ".join(sorted(missing_assets)))
        emit({"continue": True, "systemMessage": "Agent kit warning: " + "; ".join(parts)})
    return 0


def detected_secret_type(prompt: str) -> str | None:
    labels = ("private key", "AWS access key", "GitHub token", "OpenAI project key", "OpenAI API key")
    for label, pattern in zip(labels, SECRET_PATTERNS, strict=True):
        if pattern.search(prompt):
            return label
    return None


def handle_user_prompt(payload: dict) -> int:
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = ""
    secret_type = detected_secret_type(prompt)
    if secret_type:
        emit(
            {
                "decision": "block",
                "reason": f"Prompt blocked because it appears to contain a {secret_type}. Redact it and retry.",
            }
        )
    return 0


def changed_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        value = line[3:] if len(line) >= 4 else ""
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value.strip('"').replace("\\", "/"))
    return paths


def is_agent_asset(path: str) -> bool:
    return path in AGENT_ASSET_FILES or path.startswith(AGENT_ASSET_PREFIXES)


def handle_stop(payload: dict, root: Path) -> int:
    if payload.get("stop_hook_active") is True:
        return 0
    if not any(is_agent_asset(path) for path in changed_files(root)):
        return 0

    validator = root / "scripts" / "validate_agent_assets.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--root", str(root)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return 0
    diagnostic = (result.stdout + result.stderr).strip()
    if len(diagnostic) > 1200:
        diagnostic = diagnostic[-1200:]
    emit(
        {
            "decision": "block",
            "reason": "Agent asset validation failed. Fix the reported errors before stopping.\n" + diagnostic,
        }
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one Codex agent-kit hook handler.")
    parser.add_argument("event", choices=["session-start", "user-prompt-submit", "stop"])
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Repository root for validation.")
    args = parser.parse_args(argv)
    try:
        payload = read_payload()
        root = Path(args.root).resolve()
        if args.event == "session-start":
            return handle_session_start(root)
        if args.event == "user-prompt-submit":
            return handle_user_prompt(payload)
        return handle_stop(payload, root)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"Hook failed safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
