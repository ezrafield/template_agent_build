import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    from scripts.memory_evidence import EvidenceError, capture_evidence, read_source, safe_path
except ImportError:  # direct script execution
    from memory_evidence import EvidenceError, capture_evidence, read_source, safe_path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / ".agent" / "tasks"
CANDIDATES = ROOT / ".agent" / "memory" / "candidates"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "memory-candidate"


def latest_task_log() -> Path:
    logs = [path for path in TASKS.glob("*.md") if path.name != "README.md"]
    if not logs:
        raise SystemExit("No task logs found. Pass a task log path explicitly.")
    return max(logs, key=lambda path: path.stat().st_mtime)


def read_task(path_arg: str | None) -> Path:
    if not path_arg:
        return latest_task_log()
    path = Path(path_arg)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise SystemExit(f"Task log not found: {path}")
    if not path.is_file():
        raise SystemExit(f"Task log is not a file: {path}")
    try:
        return safe_path(ROOT, path.resolve().relative_to(ROOT.resolve()).as_posix())
    except (EvidenceError, ValueError) as exc:
        raise SystemExit(f"Unsafe task log: {exc}") from exc


def heading_text(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^## .+$", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def list_items(section: str) -> list[str]:
    items = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def path_like_items(items: list[str]) -> list[str]:
    paths = []
    for item in items:
        value = item.strip().strip("`")
        if not value:
            continue
        parts = value.split(maxsplit=1)
        if len(parts) == 2 and parts[0] in {"A", "M", "D", "R", "??"}:
            value = parts[1].strip().strip("`")
        if any(separator in value for separator in ["/", "\\"]) or "." in Path(value).name:
            paths.append(value)
    return paths


def first_nonempty(section: str, fallback: str) -> str:
    for line in section.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("|") and stripped != "TODO":
            return stripped
    return fallback


def relative(path: Path, root: Path = ROOT) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def candidate_body(task_path: Path, text: str, root: Path = ROOT) -> str:
    title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else task_path.stem
    goal = first_nonempty(heading_text(text, "Goal"), "TODO: summarize the reusable lesson.")
    files = path_like_items(
        list_items(heading_text(text, "Files Inspected"))
        + list_items(heading_text(text, "Changed Files"))
    )
    files = [item for item in files if item and "TODO" not in item]
    source = relative(task_path, root)
    today = date.today().isoformat()
    evidence: list[dict[str, str]] = []
    evidence_warnings: list[str] = []
    for path in dict.fromkeys(files):
        try:
            evidence.extend(capture_evidence(root, [path]))
        except (EvidenceError, OSError) as exc:
            evidence_warnings.append(f"- {path}: {exc}")

    related_files = files or [
        "TODO: add current source, test, or doc paths that verify this memory."
    ]

    return "\n".join(
        [
            f"# Memory Candidate: {title}",
            "",
            "Type: TODO: semantic or procedural",
            "Scope: TODO: project area or workflow",
            "Confidence: low",
            "Last verified: TODO: record only after reviewing the claims against current sources",
            f"Candidate generated: {today}",
            f"Source task: {source}",
            "",
            "## When to use",
            "",
            "TODO: describe the future task or situation where this memory helps.",
            "",
            "## Semantic facts learned",
            "",
            f"- TODO: extract durable facts from the task. Starting point: {goal}",
            "",
            "## Procedural lessons learned",
            "",
            "- TODO: extract reusable workflow steps, checks, or pitfalls.",
            "",
            "## Related files",
            "",
            *(f"- {item}" for item in related_files),
            "",
            "## Evidence to review",
            "",
            "These fingerprints describe current files, not verified claims. Review and select",
            "the sources that support the lesson, then copy their evidence into the index.",
            "",
            "```json",
            json.dumps(evidence, indent=2),
            "```",
            *evidence_warnings,
            "",
            "## Staleness triggers",
            "",
            "- TODO: list code, docs, tools, or workflow changes that should re-check this memory.",
            "",
            "## Promotion checklist",
            "",
            "- [ ] Contains no secrets, credentials, or private data.",
            "- [ ] Is more reusable than the raw task log.",
            "- [ ] Was verified against current files before promotion.",
            "- [ ] Was moved into semantic or procedural memory.",
            "- [ ] `.agent/memory/index.json` was updated.",
            "- [ ] Source fingerprints were refreshed after review and strict evidence validation passed.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a memory candidate from a task log.")
    parser.add_argument("task_log", nargs="?", help="Path to a .agent/tasks/*.md task log.")
    args = parser.parse_args()

    task_path = read_task(args.task_log)
    try:
        text = read_source(ROOT, relative(task_path))
    except (EvidenceError, OSError) as exc:
        parser.exit(1, f"Cannot read task log: {exc}\n")
    title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else task_path.stem
    output = CANDIDATES / f"{date.today().isoformat()}-{slugify(title)}.md"
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    output.write_text(candidate_body(task_path, text), encoding="utf-8")
    print(f"Wrote {relative(output)}")
    print("Review this candidate manually before promoting it to long-term memory.")


if __name__ == "__main__":
    main()
