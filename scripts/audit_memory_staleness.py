import argparse
from datetime import date
from pathlib import Path

try:
    from scripts.memory_evidence import EvidenceError, inspect_evidence, read_source, safe_path
    from scripts.validate_memory_links import as_path, legacy_relative, load_index, related_files
except ImportError:  # direct script execution
    from memory_evidence import EvidenceError, inspect_evidence, read_source, safe_path
    from validate_memory_links import as_path, legacy_relative, load_index, related_files


ROOT = Path(__file__).resolve().parents[1]
MAX_AGE_DAYS = 180


def audit(root: Path = ROOT, today: date | None = None) -> tuple[list[str], list[str]]:
    today = today or date.today()
    warnings: list[str] = []
    statuses: list[str] = []
    try:
        data = load_index(root)
    except (EvidenceError, OSError, ValueError) as exc:
        return [f"Cannot read memory index: {exc}"], statuses
    memories = data.get("memories", [])
    if not isinstance(memories, list):
        return ["index memories must be a list"], statuses

    for entry in memories:
        if not isinstance(entry, dict):
            warnings.append("memory entry is not an object")
            continue
        entry_id = entry.get("id", "<missing id>")
        issues: list[str] = []
        try:
            verified_date = date.fromisoformat(entry.get("last_verified"))
            age_days = (today - verified_date).days
            if age_days > MAX_AGE_DAYS:
                issues.append(f"last verified {age_days} days ago")
            elif age_days < 0:
                issues.append("last_verified is in the future")
        except (TypeError, ValueError):
            issues.append(f"invalid last_verified date: {entry.get('last_verified')}")

        try:
            text = read_source(root, legacy_relative(entry.get("path")))
            for related in related_files(text):
                if not as_path(related, root).is_file():
                    issues.append(f"related file no longer exists: {related}")
        except (EvidenceError, OSError) as exc:
            issues.append(str(exc))

        evidence = inspect_evidence(root, entry)
        status = evidence.status
        if status not in {"unchanged", "untracked"}:
            issues.extend(evidence.details)
        elif issues:
            status = "needs-reverification"
        statuses.append(f"{entry_id}: {status}")
        warnings.extend(f"{entry_id}: {issue}" for issue in issues)
    return warnings, statuses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check memory age, missing sources, and evidence drift.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    warnings, statuses = audit(args.root)
    for status in statuses:
        print(status)
    for warning in warnings:
        print(warning)
    if warnings:
        return 1
    print("Memory audit passed; untracked entries still require manual source verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
