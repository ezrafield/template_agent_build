import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    commands = [
        [sys.executable, "scripts/validate_agent_assets.py"],
        [sys.executable, "eval/agent/run_hook_eval.py"],
        [sys.executable, "eval/skills/run_skill_routing_eval.py", "--validate-only"],
    ]
    failures: list[str] = []
    for command in commands:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            failures.append(" ".join(command))
    if failures:
        print("Agent eval failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Deterministic agent evals passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
