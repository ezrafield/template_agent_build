from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CARDS = ROOT / "docs" / "agent" / "module-cards"


TEMPLATE = """# Module: {name}

## Responsibility
TODO - describe this module's responsibility.

## Key Files
{files}

## Public Interfaces
- TODO

## Rules
- Follow existing project boundaries.

## Common Tasks
- TODO

## Known Pitfalls
- TODO
"""


def main() -> None:
    CARDS.mkdir(parents=True, exist_ok=True)
    created = []

    for directory in sorted(
        path
        for path in SRC.iterdir()
        if path.is_dir() and path.name != "__pycache__" and not path.name.startswith(".")
    ):
        card = CARDS / f"{directory.name}.md"
        if card.exists():
            continue

        files = sorted(
            path.relative_to(ROOT).as_posix()
            for path in directory.rglob("*.py")
            if "__pycache__" not in path.parts
        )
        file_lines = "\n".join(f"- `{file}`" for file in files) if files else "- TODO"
        card.write_text(
            TEMPLATE.format(name=directory.name.title(), files=file_lines),
            encoding="utf-8",
        )
        created.append(card.relative_to(ROOT).as_posix())

    if created:
        print("Created module cards:")
        for path in created:
            print(f"- {path}")
    else:
        print("No missing module cards.")


if __name__ == "__main__":
    main()
