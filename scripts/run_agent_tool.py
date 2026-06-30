import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_ROOT = ROOT / "tools" / "agent"


def is_windows() -> bool:
    return os.name == "nt"


def tool_dirs() -> list[Path]:
    return [
        TOOL_ROOT / "bin",
        TOOL_ROOT / "python" / "semble" / ".venv" / ("Scripts" if is_windows() else "bin"),
        TOOL_ROOT / "python" / "serena" / ".venv" / ("Scripts" if is_windows() else "bin"),
        TOOL_ROOT / "node_modules" / ".bin",
    ]


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    dirs = [str(path) for path in tool_dirs() if path.exists()]
    current_path = env.get("PATH", "")
    env["PATH"] = os.pathsep.join(dirs + ([current_path] if current_path else []))
    env.setdefault("SEMBLE_CACHE_LOCATION", str(ROOT / ".agent" / "context-cache" / "semble"))
    env.setdefault("HF_HOME", str(TOOL_ROOT / ".hf-cache"))
    env.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    return env


def parse_args(argv: list[str]) -> tuple[list[str] | None, str, list[str]]:
    fallback: list[str] | None = None
    if argv[:1] == ["--fallback"]:
        try:
            separator = argv.index("--", 1)
        except ValueError:
            print("Usage: run_agent_tool.py --fallback <raw command...> -- <tool> [args...]", file=sys.stderr)
            raise SystemExit(2)
        fallback = argv[1:separator]
        argv = argv[separator + 1 :]

    if not argv:
        print("Usage: run_agent_tool.py [--fallback <raw command...> --] <tool> [args...]", file=sys.stderr)
        raise SystemExit(2)

    return fallback, argv[0], argv[1:]


def find_tool(tool: str, env: dict[str, str]) -> str | None:
    return shutil.which(tool, path=env.get("PATH"))


def prepare_command(command: list[str]) -> list[str]:
    executable = Path(command[0])
    if is_windows() and executable.suffix.lower() in {".bat", ".cmd"}:
        return [os.environ.get("ComSpec", "cmd.exe"), "/d", "/c", command[0], *command[1:]]
    return command


def run(command: list[str], env: dict[str, str]) -> int:
    return subprocess.run(prepare_command(command), cwd=ROOT, env=env, check=False).returncode


def main() -> None:
    fallback, tool, tool_args = parse_args(sys.argv[1:])
    env = build_env()
    executable = find_tool(tool, env)
    if tool == "semble":
        Path(env["SEMBLE_CACHE_LOCATION"]).mkdir(parents=True, exist_ok=True)

    if executable:
        raise SystemExit(run([executable, *tool_args], env))

    if fallback is not None:
        print(f"{tool} not found; running raw fallback: {' '.join(fallback)}", file=sys.stderr)
        raise SystemExit(run(fallback, env))

    print(
        f"{tool} not found in project-local tools or PATH. Run `make agent-tools-install`.",
        file=sys.stderr,
    )
    raise SystemExit(127)


if __name__ == "__main__":
    main()
