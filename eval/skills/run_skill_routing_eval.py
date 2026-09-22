import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "eval" / "skills" / "routing_cases.json"


def skill_names(root: Path) -> set[str]:
    return {path.parent.name for path in (root / ".agents" / "skills").glob("*/SKILL.md")}


def validate_cases(root: Path, cases: list[dict]) -> list[str]:
    errors: list[str] = []
    known = skill_names(root)
    ids: list[str] = []
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("Every routing case requires a non-empty id.")
            continue
        ids.append(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"{case_id}: prompt must be a non-empty string.")
        for field_name in ("expected", "allowed", "forbidden"):
            values = case.get(field_name)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                errors.append(f"{case_id}: {field_name} must be a string list.")
                continue
            unknown = set(values) - known
            if unknown:
                errors.append(f"{case_id}: unknown {field_name} skills: {sorted(unknown)}.")
        expected = set(case.get("expected", []))
        allowed = set(case.get("allowed", []))
        forbidden = set(case.get("forbidden", []))
        if not expected:
            errors.append(f"{case_id}: expected must contain at least one skill.")
        if expected & allowed or expected & forbidden or allowed & forbidden:
            errors.append(f"{case_id}: expected, allowed, and forbidden sets must be disjoint.")
    if len(ids) != len(set(ids)):
        errors.append("Routing case ids must be unique.")
    return errors


def extract_agent_json(output: str) -> dict:
    messages: list[str] = []
    for line in output.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = item.get("item") if isinstance(item, dict) else None
        if isinstance(payload, dict) and payload.get("type") == "agent_message":
            text = payload.get("text")
            if isinstance(text, str):
                messages.append(text)
    if not messages:
        raise ValueError("Codex emitted no agent_message item.")
    value = messages[-1].strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Codex routing response must be a JSON object.")
    return parsed


def route_case(
    codex: str,
    root: Path,
    case: dict,
    known: set[str],
    model: str,
    timeout: int = 300,
) -> set[str]:
    prompt = (
        "This is a skill-routing evaluation. Do not perform the task and do not edit files. "
        "Select the repository skills you would activate for the quoted request. Return only "
        'JSON shaped as {"selected_skills":["skill-name"]}. Use only these names: '
        + ", ".join(sorted(known))
        + ". Request: "
        + json.dumps(case["prompt"])
    )
    result = subprocess.run(
        [
            codex,
            "exec",
            "--json",
            "--model",
            model,
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-rules",
            "--disable",
            "hooks",
            "-c",
            'approval_policy="never"',
            prompt,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    parsed = extract_agent_json(result.stdout)
    selected = parsed.get("selected_skills")
    if not isinstance(selected, list) or not all(isinstance(value, str) for value in selected):
        raise ValueError("selected_skills must be a string list.")
    unknown = set(selected) - known
    if unknown:
        raise ValueError(f"Codex selected unknown skills: {sorted(unknown)}")
    return set(selected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill-routing fixtures offline; opt in to Codex trials with --live --model MODEL.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Run authenticated Codex routing trials after fixture validation.")
    mode.add_argument("--validate-only", action="store_true", help="Alias for the default offline fixture validation; conflicts with --live.")
    parser.add_argument("--model", help="Explicit Codex model required for --live; does not enable live trials by itself.")
    parser.add_argument("--limit", type=int, help="Run only the first N live cases; offline validation always checks the full corpus.")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum seconds per live case; no retries.")
    args = parser.parse_args(argv)
    if args.timeout < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--timeout and --limit must be positive")
    if args.live and (not args.model or not args.model.strip()):
        parser.error("--live requires an explicit non-empty --model")
    root = Path(args.root).resolve()
    cases = json.loads((root / CASES.relative_to(ROOT)).read_text(encoding="utf-8"))
    errors = validate_cases(root, cases)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"Skill routing fixtures valid: {len(cases)} cases, {len(skill_names(root))} skills.")
    if not args.live:
        return 0

    codex = shutil.which("codex")
    if not codex:
        print("Skill routing eval requires an authenticated Codex CLI.", file=sys.stderr)
        return 2
    selected_cases = cases[: args.limit] if args.limit is not None else cases
    known = skill_names(root)
    expected_total = 0
    expected_hits = 0
    unexpected_total = 0
    forbidden_total = 0
    collision_cases = 0
    failures: list[str] = []
    for case in selected_cases:
        expected = set(case["expected"])
        # A failed invocation is a miss, never removed from recall's denominator.
        expected_total += len(expected)
        try:
            selected = route_case(codex, root, case, known, args.model, args.timeout)
        except subprocess.TimeoutExpired:
            failures.append(f"{case['id']}: timed out after {args.timeout}s (no retry)")
            continue
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"{case['id']}: {exc}")
            continue
        allowed = set(case["allowed"])
        forbidden = set(case["forbidden"])
        hits = selected & expected
        unexpected = selected - expected - allowed
        forbidden_hits = selected & forbidden
        expected_hits += len(hits)
        unexpected_total += len(unexpected)
        forbidden_total += len(forbidden_hits)
        if unexpected or forbidden_hits:
            collision_cases += 1
        print(f"{case['id']}: selected={sorted(selected)} expected={sorted(expected)}")

    precision_denominator = expected_hits + unexpected_total
    precision = expected_hits / precision_denominator if precision_denominator else 0.0
    recall = expected_hits / expected_total if expected_total else 0.0
    collision_rate = collision_cases / len(selected_cases) if selected_cases else 0.0
    print(f"precision={precision:.3f}")
    print(f"recall={recall:.3f}")
    print(f"collision_rate={collision_rate:.3f}")
    print(f"forbidden_activations={forbidden_total}")
    print(f"completed_cases={len(selected_cases) - len(failures)}")
    print(f"failed_cases={len(failures)}")
    print("Live skill-routing quality metrics are informational; failures remain explicit.")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
