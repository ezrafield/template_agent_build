from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CARDS = ROOT / "docs" / "agent" / "module-cards"
REQUIRED_HEADINGS = ["## Responsibility", "## Key Files", "## Public Interfaces", "## Rules"]


def main() -> None:
    problems = []
    if SRC.exists():
        for directory in sorted(
            path
            for path in SRC.iterdir()
            if path.is_dir() and path.name != "__pycache__" and not path.name.startswith(".")
        ):
            card = CARDS / f"{directory.name}.md"
            if not card.exists():
                problems.append(f"Missing module card for {directory.relative_to(ROOT).as_posix()}/")
                continue
            text = card.read_text(encoding="utf-8")
            for heading in REQUIRED_HEADINGS:
                if heading not in text:
                    problems.append(f"{card.relative_to(ROOT).as_posix()} missing {heading}")
            if "TODO" in text:
                problems.append(f"{card.relative_to(ROOT).as_posix()} still contains TODO")

    if problems:
        for problem in problems:
            print(problem)
        raise SystemExit(1)

    print("Module cards cover source modules and required headings.")


if __name__ == "__main__":
    main()
