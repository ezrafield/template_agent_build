from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / ".agent" / "tasks"
REQUIRED_HEADINGS = [
    "## Goal",
    "## Commands Run",
    "## Token / Context Notes",
    "## Verification",
    "## Memory Extraction",
    "## Follow-Up",
]
CHECKPOINT_FIELDS = (
    "Linked plan", "Completed acceptance criteria", "Outstanding material findings",
    "Review independence", "Verified revision and dirty-file state",
    "Verification link or new checks/results", "External effects already performed",
    "Next action and checks invalidated by later edits",
)


def missing_requirements(text: str) -> list[str]:
    """Accept legacy logs or a complete concise resume checkpoint."""
    headings = set(re.findall(r"^## .+$", text, re.MULTILINE))
    missing = [f"missing {heading}" for heading in REQUIRED_HEADINGS if heading not in headings]
    if not missing or "## Review And Checkpoint" not in headings:
        return missing
    section = re.split(r"^## Review And Checkpoint\s*$", text, maxsplit=1, flags=re.MULTILINE)[1]
    section = re.split(r"^## ", section, maxsplit=1, flags=re.MULTILINE)[0]
    problems = []
    for label in CHECKPOINT_FIELDS:
        match = re.search(r"^- " + re.escape(label) + r":[ \t]*(.*)$", section, re.MULTILINE)
        if not match or not match[1].strip() or re.search(r"\bTODO\b", match[1], re.IGNORECASE):
            problems.append(f"checkpoint requires completed '{label}'")
    return problems


def main() -> None:
    problems = []
    if not TASKS.exists():
        print(".agent/tasks does not exist.")
        return

    for path in sorted(TASKS.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        problems.extend(f"{path.relative_to(ROOT).as_posix()} {problem}" for problem in missing_requirements(text))

    if problems:
        for problem in problems:
            print(problem)
        raise SystemExit(1)

    print("Task logs include legacy audit headings or complete concise checkpoints.")


if __name__ == "__main__":
    main()
