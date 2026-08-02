from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DOCS = [
    "docs/agent/CODEMAP.md",
]
SOURCE_DIRS = [
    "src",
    "tests",
]


def newest_source_mtime() -> float:
    mtimes = []
    for directory_name in SOURCE_DIRS:
        directory = ROOT / directory_name
        if directory.exists():
            mtimes.extend(
                path.stat().st_mtime
                for path in directory.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            )
    return max(mtimes, default=0)


def main() -> None:
    newest = newest_source_mtime()
    stale = []
    for relative in GENERATED_DOCS:
        path = ROOT / relative
        if not path.exists():
            stale.append(f"{relative} is missing")
        elif newest and path.stat().st_mtime < newest:
            stale.append(f"{relative} may be older than source files")

    if stale:
        for message in stale:
            print(message)
        raise SystemExit(1)

    print("Generated agent context is not older than source files.")


if __name__ == "__main__":
    main()
