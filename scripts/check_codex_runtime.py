import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def run_case(codex: str, rules: Path, case: dict, root: Path) -> str | None:
    command = case.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        return f"{case.get('id', '<unknown>')}: command must be a non-empty string list"
    result = subprocess.run(
        [codex, "execpolicy", "check", "--pretty", "--rules", str(rules), "--", *command],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"{case.get('id')}: execpolicy failed: {result.stderr.strip() or result.stdout.strip()}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return f"{case.get('id')}: invalid execpolicy JSON: {exc}"
    actual_decision = output.get("decision")
    actual_matches = len(output.get("matchedRules", []))
    if actual_decision != case.get("expected_decision"):
        return (
            f"{case.get('id')}: expected decision {case.get('expected_decision')!r}, "
            f"got {actual_decision!r}"
        )
    if actual_matches != case.get("expected_match_count"):
        return (
            f"{case.get('id')}: expected {case.get('expected_match_count')} matches, "
            f"got {actual_matches}"
        )
    print(f"PASS {case.get('id')}: decision={actual_decision!r}, matches={actual_matches}")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Codex hooks support and execpolicy rules.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Repository root to check.")
    parser.add_argument("--codex", help="Codex executable path; defaults to PATH lookup.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    codex = args.codex or shutil.which("codex")
    if not codex:
        print("Codex runtime check skipped: codex is not installed.", file=sys.stderr)
        return 2

    version = subprocess.run([codex, "--version"], check=False, capture_output=True, text=True)
    if version.returncode != 0:
        print(version.stderr.strip() or "Unable to read Codex version.", file=sys.stderr)
        return 1
    print(version.stdout.strip())

    features = subprocess.run([codex, "features", "list"], check=False, capture_output=True, text=True)
    if features.returncode != 0 or not any(
        line.split()[:1] == ["hooks"] and "true" in line.split()[2:]
        for line in features.stdout.splitlines()
    ):
        print("Codex hooks feature is unavailable or disabled.", file=sys.stderr)
        return 1

    rules = root / ".codex" / "templates" / "default.rules"
    cases_path = root / "eval" / "rules" / "command_cases.json"
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot load rule cases: {exc}", file=sys.stderr)
        return 1

    failures = [failure for case in cases if (failure := run_case(codex, rules, case, root))]
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"Codex runtime check passed: {len(cases)} rule cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
