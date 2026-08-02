import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "eval" / "agent" / "hook_cases.json"
HANDLER = ROOT / "scripts" / "run_agent_hook.py"


def fixture_root(kind: str | None, temporary_root: Path) -> Path:
    if kind is None:
        return ROOT
    (temporary_root / "docs" / "agent").mkdir(parents=True, exist_ok=True)
    (temporary_root / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")
    (temporary_root / "docs" / "agent" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    commands = [] if kind == "healthy" else ["definitely-missing-agent-command"]
    (temporary_root / "agentkit-manifest.json").write_text(
        json.dumps({"runtime": {"required_commands": commands}}),
        encoding="utf-8",
    )
    return temporary_root


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="agent-hook-eval-") as temp_name:
        temp_root = Path(temp_name)
        for case in cases:
            root = fixture_root(case.get("fixture"), temp_root)
            result = subprocess.run(
                [sys.executable, str(HANDLER), case["event"], "--root", str(root)],
                input=json.dumps(case.get("payload", {})),
                check=False,
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()
            if result.returncode != 0:
                failures.append(f"{case['id']}: exited {result.returncode}: {result.stderr.strip()}")
                continue
            if "expected_stdout" in case and output != case["expected_stdout"]:
                failures.append(f"{case['id']}: expected stdout {case['expected_stdout']!r}, got {output!r}")
                continue
            if expected := case.get("expected_json_fields"):
                try:
                    parsed = json.loads(output)
                except json.JSONDecodeError:
                    failures.append(f"{case['id']}: expected JSON output, got {output!r}")
                    continue
                if any(parsed.get(key) != value for key, value in expected.items()):
                    failures.append(f"{case['id']}: expected fields {expected}, got {parsed}")
                    continue
            forbidden = case.get("forbidden_output")
            if forbidden and forbidden in result.stdout + result.stderr:
                failures.append(f"{case['id']}: secret-like input leaked into output")
                continue
            print(f"PASS {case['id']}")

    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"Hook eval passed: {len(cases)} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
