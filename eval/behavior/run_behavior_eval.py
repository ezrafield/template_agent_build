"""Offline behavioral fixtures and opt-in, matched Codex workflow trials.

Reports deliberately contain metrics and evaluator diagnostics only, never raw
agent events, prompts, credentials, or hidden reasoning.
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
ARTIFACTS = Path(".agent/traces/evals")
RUNTIME_PREFIXES = (".agent/context-cache/", ".agent/traces/", ".agent/plans/", ".agent/tasks/")


def safe_path(root: Path, value: str) -> Path:
    pure = PurePosixPath(value)
    if not value or "\\" in value or ":" in value or pure.is_absolute() or ".." in pure.parts:
        raise ValueError("Fixture paths must be relative and contained in the workspace.")
    target = root.joinpath(*pure.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Fixture path escapes the workspace.")
    return target


def copy_tree(source: Path, target: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Evaluation inputs cannot contain symbolic links.")
        if path.is_file() and "__pycache__" not in path.parts:
            destination = safe_path(target, path.relative_to(source).as_posix())
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def load_cases(fixtures: Path = FIXTURES) -> list[dict]:
    cases = []
    for manifest in sorted(fixtures.glob("*/case.json")):
        case = json.loads(manifest.read_text(encoding="utf-8"))
        case["directory"] = manifest.parent
        if case.get("id") != manifest.parent.name or not isinstance(case.get("request"), str):
            raise ValueError("Each fixture requires its directory ID and a request.")
        permitted = case.get("permitted_changes")
        if not isinstance(permitted, list) or not permitted:
            raise ValueError(f"{case['id']}: permitted_changes must be a nonempty path list.")
        for value in permitted:
            safe_path(manifest.parent, value)
        for name in ("initial", "reference"):
            if not (manifest.parent / name).is_dir():
                raise ValueError(f"{case['id']}: missing {name} repository files.")
        if not (manifest.parent / "acceptance.py").is_file():
            raise ValueError(f"{case['id']}: missing external acceptance checks.")
        cases.append(case)
    if not cases:
        raise ValueError("No behavioral fixtures found.")
    return cases


def snapshot(root: Path) -> dict[str, str]:
    result = {}
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        names[:] = sorted(name for name in names if name not in {".git", "__pycache__", ".pytest_cache"})
        # A symlink directory is itself an observable change, not a tree to follow.
        for name in list(names):
            path = base / name
            if path.is_symlink():
                result[path.relative_to(root).as_posix()] = "symlink:" + os.readlink(path)
                names.remove(name)
        for name in sorted(files):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[relative] = "symlink:" + os.readlink(path)
            else:
                result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    # Commits or configuration changes must not hide behind an unchanged diff.
    git_root = root / ".git"
    if git_root.is_dir() and not git_root.is_symlink():
        git_paths = [git_root / name for name in ("HEAD", "config", "packed-refs")]
        git_paths.extend((git_root / "refs").rglob("*"))
        for path in git_paths:
            if path.is_symlink():
                result[path.relative_to(root).as_posix()] = "symlink:" + os.readlink(path)
            elif path.is_file():
                result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def diff_scope(before: dict, after: dict, permitted: list[str]) -> tuple[list[str], list[str]]:
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    # Workflow output may be created, but pre-existing policy, task or memory
    # files remain protected. Caches are explicitly disposable in both arms.
    def allowed(path: str) -> bool:
        return path in permitted or path.startswith((".agent/context-cache/", ".agent/traces/")) or (
            path not in before and path.startswith(RUNTIME_PREFIXES)
        )

    return changed, [path for path in changed if not allowed(path)]


def run_process(arguments: list[str], cwd: Path, timeout: int, env: dict | None = None) -> dict:
    """Bound the whole command tree so a timeout cannot leave Codex editing."""
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    started = time.monotonic()
    process = subprocess.Popen(arguments, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **options)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        stdout, stderr = process.communicate()
    return {"returncode": process.returncode, "stdout": stdout, "stderr": stderr, "timed_out": timed_out, "elapsed_seconds": round(time.monotonic() - started, 3)}


def grade(case: dict, workspace: Path, before: dict, process_runner=run_process) -> dict:
    changed, violations = diff_scope(before, snapshot(workspace), case["permitted_changes"])
    # Copy checks outside the writable agent workspace. Check their integrity
    # after execution as well; these are controlled tasks, not an adversarial
    # code-execution security sandbox.
    with tempfile.TemporaryDirectory(prefix="behavior-check-") as temporary:
        check = Path(temporary) / "acceptance.py"
        shutil.copy2(case["directory"] / "acceptance.py", check)
        digest = hashlib.sha256(check.read_bytes()).digest()
        result = process_runner([sys.executable, "-I", "-B", str(check), str(workspace)], Path(temporary), 30)
        intact = check.is_file() and hashlib.sha256(check.read_bytes()).digest() == digest
    # Check after grading too: imported candidate code must not mutate files.
    _, after_violations = diff_scope(before, snapshot(workspace), case["permitted_changes"])
    violations = sorted(set(violations + after_violations))
    checks_passed = result["returncode"] == 0 and not result["timed_out"] and intact
    check_lines = re.findall(r'File "[^"\r\n]*acceptance\.py", line (\d+)', result.get("stderr", ""))
    # Preserve actionable checker locations, not candidate-controlled messages.
    diagnostics = {"exit_code": result["returncode"], "check_lines": [int(line) for line in check_lines]}
    failure = None if checks_passed else ("timeout" if result["timed_out"] else ("checks_failed" if intact else "check_integrity_changed"))
    return {"correct": checks_passed and not violations, "acceptance_passed": checks_passed, "acceptance_failure": failure, "acceptance_diagnostics": diagnostics, "changed_files": changed, "scope_violations": violations}


def event_metrics(output: str) -> dict:
    commands = set()
    usage = None
    failed = False
    completed = False
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") in {"turn.failed", "error"}:
            failed = True
        item = event.get("item", {})
        if isinstance(item, dict) and item.get("type") == "command_execution" and item.get("id"):
            commands.add(str(item["id"]))
        if event.get("type") == "turn.completed":
            completed = True
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = {
                key: value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
                for key in ("input_tokens", "cached_input_tokens", "output_tokens")
                for value in [event["usage"].get(key)]
            }
    return {"command_count": len(commands) if commands or completed else None, "usage": usage, "cost": None, "agent_failed": failed, "telemetry_complete": completed}


def trial_prompt(case: dict) -> str:
    return (
        "Complete this repository task using its installed agent instructions. "
        "Do not make network requests, install packages, commit, or change guardrails. "
        "Acceptance is checked independently. Only these project files may change: "
        + ", ".join(case["permitted_changes"])
        + ". New task/plan notes and ignored context caches are permitted; keep existing instructions and memories unless explicitly listed. "
        + "Use the Python interpreter " + sys.executable + " for Python commands. Task: " + case["request"]
    )


def reading_context_characters(workspace: Path) -> int | None:
    """Estimate available reading artifacts, counting one view per identity.

    This does not establish whether the agent read a bundle or measure tokens.
    Legacy baseline builds have only the full Markdown artifact.
    """
    selected: dict[str, Path] = {}
    cache = workspace / ".agent/context-cache/task-context"
    for path in sorted(cache.glob("*.md")):
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(workspace.resolve()):
            continue
        compact = path.name.endswith(".read.md")
        identity = path.name[:-len(".read.md")] if compact else path.stem
        if compact or identity not in selected:
            selected[identity] = path
    if not selected:
        return None
    try:
        return sum(len(path.read_text(encoding="utf-8")) for path in selected.values())
    except (OSError, UnicodeError):
        return None


def run_trial(case: dict, source: Path, arm: str, model: str, codex: str, timeout: int = 300, runner=run_process, prepare=None) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"behavior-{arm}-") as temporary:
        workspace = Path(temporary) / "project"
        workspace.mkdir()
        copy_tree(case["directory"] / "initial", workspace)
        (prepare or prepare_workspace)(source, workspace)
        before = snapshot(workspace)
        arguments = [codex, "exec", "--json", "--sandbox", "workspace-write", "--ephemeral", "--enable", "hooks", "--model", model, "-c", 'approval_policy="never"', "-c", "sandbox_workspace_write.network_access=false", trial_prompt(case)]
        try:
            outcome = runner(arguments, workspace, timeout)
            metrics = event_metrics(outcome["stdout"])
            failure = "timeout" if outcome["timed_out"] else ("agent_failed" if outcome["returncode"] or metrics["agent_failed"] else (None if metrics["telemetry_complete"] else "missing_completion_event"))
        except OSError:
            outcome = {"elapsed_seconds": 0}
            metrics = event_metrics("")
            failure = "runner_unavailable"
        judged = grade(case, workspace, before)
        context_characters = reading_context_characters(workspace)
        judged["correct"] = judged["correct"] and failure is None
        return {"case": case["id"], "arm": arm, "failure": failure, "elapsed_seconds": outcome["elapsed_seconds"], "context_characters": context_characters, "context_measurement": "available_generated_reading_characters_estimate", **metrics, **judged}


def checked(arguments: list[str], cwd: Path) -> str:
    result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, timeout=60)
    if result.returncode:
        # Avoid logging tool output which may contain host credentials or paths.
        operation = Path(arguments[1]).name if len(arguments) > 1 else Path(arguments[0]).name
        raise RuntimeError(f"Evaluation preparation failed: {operation} (exit {result.returncode}).")
    return result.stdout.strip()


def prepare_workspace(source: Path, workspace: Path) -> None:
    checked([sys.executable, str(source / "scripts/agentkit_installer.py"), "install", "--source", str(source), "--target", str(workspace)], source)
    checked(["git", "init", "--quiet"], workspace)
    # The evaluation activates the same installed guardrail mechanism in both
    # arms. Host hook trust remains in effect; it is never bypassed by the runner.
    checked([sys.executable, "scripts/enable_codex_guardrails.py", "--target", str(workspace)], workspace)
    checked(["git", "add", "."], workspace)
    checked(["git", "-c", "user.name=Behavior Evaluator", "-c", "user.email=behavior@example.invalid", "commit", "--quiet", "-m", "Evaluation starting state"], workspace)


def capture_sources(root: Path, baseline_ref: str, destination: Path) -> tuple[dict, dict]:
    revision = checked(["git", "rev-parse", "--verify", baseline_ref + "^{commit}"], root)
    archived = subprocess.run(["git", "archive", "--format=zip", revision], cwd=root, capture_output=True, check=True, timeout=60).stdout
    baseline = destination / "baseline"
    baseline.mkdir()
    with zipfile.ZipFile(io.BytesIO(archived)) as archive:
        for member in archive.infolist():
            target = safe_path(baseline, member.filename.rstrip("/"))
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
    sys.path.insert(0, str(root))
    from scripts.agentkit_installer import iter_manifest_paths

    candidate = destination / "candidate"
    candidate.mkdir()
    manifest = json.loads((root / "agentkit-manifest.json").read_text(encoding="utf-8"))
    entries = manifest["included_harness_files"] + manifest["copy_if_missing_files"] + manifest["merge_files"]
    for path in iter_manifest_paths(root, entries, manifest["excluded_files"]):
        if path.is_symlink():
            raise ValueError("Candidate kit contains a symbolic link.")
        target = safe_path(candidate, path.relative_to(root).as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    # Keep reference answers and evaluator checks outside both agent workspaces.
    for source in (baseline, candidate):
        manifest_path = source / "agentkit-manifest.json"
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        value.setdefault("excluded_files", []).append("eval/behavior/fixtures/")
        manifest_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    candidate_hash = hashlib.sha256(json.dumps(snapshot(candidate), sort_keys=True).encode()).hexdigest()
    return {"baseline": baseline, "candidate": candidate}, {"baseline_revision": revision, "candidate_head": checked(["git", "rev-parse", "HEAD"], root), "candidate_snapshot_sha256": candidate_hash, "evaluation_corpus_installed": False}


def offline(cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="behavior-reference-") as temporary:
            workspace = Path(temporary)
            copy_tree(case["directory"] / "initial", workspace)
            before = snapshot(workspace)
            initial = grade(case, workspace, before)
            copy_tree(case["directory"] / "reference", workspace)
            reference = grade(case, workspace, before)
            results.append({"case": case["id"], "initial_rejected": not initial["correct"], "reference_passed": reference["correct"], "scope_violations": reference["scope_violations"], "reference_failure": reference["acceptance_failure"], "reference_diagnostics": reference["acceptance_diagnostics"]})
    return results


def sanitize(value):
    if isinstance(value, dict):
        return {sanitize(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|AKIA[A-Z0-9]{16})", "<REDACTED>", value)
        value = re.sub(r"(?i)(https?://)[^\s/@]+:[^\s/@]+@", r"\1<REDACTED>@", value)
        value = re.sub(r"(?i)\b(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+", r"\1=<REDACTED>", value)
    return value


def write_report(root: Path, report: dict) -> Path:
    directory = root / ARTIFACTS
    directory.mkdir(parents=True, exist_ok=True)
    # Only constructed metrics reach this function. Never persist subprocess
    # stdout, stderr, agent messages, commands or reasoning event bodies.
    path = directory / f"behavior-{time.time_ns()}.json"
    path.write_text(json.dumps(sanitize(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--baseline-ref")
    parser.add_argument("--case", action="append", default=[], dest="cases")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    if args.live and (not args.model or not args.baseline_ref):
        parser.error("--live requires explicit --model and --baseline-ref")
    if args.repeat < 1 or args.timeout < 1:
        parser.error("--repeat and --timeout must be positive")
    root = Path(args.root).resolve()
    try:
        cases = load_cases(root / "eval/behavior/fixtures")
        unknown = set(args.cases) - {case["id"] for case in cases}
        if unknown:
            parser.error("unknown case IDs: " + ", ".join(sorted(unknown)))
        cases = [case for case in cases if not args.cases or case["id"] in args.cases]
        references = offline(cases)
        if not all(row["initial_rejected"] and row["reference_passed"] for row in references):
            print(json.dumps(references, indent=2))
            return 1
        print(f"Behavior fixtures valid: {len(cases)} cases; initial solutions rejected; reference solutions pass.")
        if not args.live:
            return 0
        codex = shutil.which("codex")
        if not codex:
            print("Live behavior evaluation requires an authenticated Codex CLI.", file=sys.stderr)
            return 2
        results = []
        with tempfile.TemporaryDirectory(prefix="behavior-sources-") as temporary:
            sources, provenance = capture_sources(root, args.baseline_ref, Path(temporary))
            for repetition in range(args.repeat):
                for index, case in enumerate(cases):
                    # Alternate order without changing tasks or limits.
                    arms = ("baseline", "candidate") if (index + repetition) % 2 == 0 else ("candidate", "baseline")
                    for arm in arms:
                        try:
                            row = run_trial(case, sources[arm], arm, args.model, codex, args.timeout)
                        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
                            row = {"case": case["id"], "arm": arm, "correct": False, "failure": "preparation_or_grading_failed", "failure_detail": sanitize(f"{type(exc).__name__}: {exc}"), "scope_violations": [], "usage": None, "cost": None, "command_count": None, "context_characters": None, "elapsed_seconds": None}
                            print(f"FAIL {case['id']} {arm}: {row['failure_detail']}", file=sys.stderr)
                        row["repetition"] = repetition + 1
                        results.append(row)
                        print(f"{case['id']} {arm}: correct={row['correct']} failure={row['failure']}")
        summary = {arm: {"trials": sum(row["arm"] == arm for row in results), "successes": sum(row["arm"] == arm and row["correct"] for row in results), "failed_trials": sum(row["arm"] == arm and row["failure"] is not None for row in results), "scope_violations": sum(len(row["scope_violations"]) for row in results if row["arm"] == arm)} for arm in ("baseline", "candidate")}
        report = {"schema_version": 1, "model": args.model, "timeout_seconds": args.timeout, "repetitions": args.repeat, "permissions": "workspace-write; approval never; hooks enabled; host trust retained", "effectiveness": "requires human review of matched results; small samples are uncertain", "provenance": provenance, "summary": summary, "trials": results}
        path = write_report(root, report)
        print(f"Report: {path.relative_to(root).as_posix()}")
        # Behavioral quality is informational. Infrastructure failures remain
        # nonzero so absent results cannot masquerade as a successful run.
        return 1 if any(row["failure"] for row in results) else 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Behavior evaluation failed during fixture or snapshot preparation: {sanitize(f'{type(exc).__name__}: {exc}')}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
