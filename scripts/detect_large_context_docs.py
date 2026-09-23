from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_LINES = 200
AUTO_LOADED_DOCS = [
    "AGENTS.md",
    "src/AGENTS.md",
    "tests/AGENTS.md",
]


def main() -> None:
    failed = False
    for relative_path in AUTO_LOADED_DOCS:
        path = ROOT / relative_path
        if not path.exists():
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_LINES:
            print(f"{relative_path}: {line_count} lines exceeds {MAX_LINES}.")
            failed = True
        else:
            print(f"{relative_path}: {line_count} lines.")

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
