import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    from scripts.memory_evidence import EvidenceError, inspect_evidence, read_source, safe_path
except ImportError:  # direct script execution
    from memory_evidence import EvidenceError, inspect_evidence, read_source, safe_path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / ".agent" / "memory" / "index.json"
VALID_TYPES = {"semantic", "procedural"}
VALID_CONFIDENCE = {"high", "medium", "low"}
REQUIRED_ENTRY_FIELDS = {
    "id",
    "type",
    "scope",
    "path",
    "summary",
    "keywords",
    "confidence",
    "last_verified",
    "source_task",
}
REQUIRED_CARD_FIELDS = {
    "Type",
    "Scope",
    "Confidence",
    "Last verified",
    "Source task",
}
REQUIRED_HEADINGS = {"When to use", "Related files", "Staleness triggers"}


def load_index(root: Path = ROOT) -> dict[str, Any]:
    value = json.loads(read_source(root, ".agent/memory/index.json"))
    if not isinstance(value, dict):
        raise ValueError("memory index must be an object")
    return value


def as_path(relative: str, root: Path = ROOT) -> Path:
    return safe_path(root, legacy_relative(relative))


def legacy_relative(relative: str) -> str:
    # Legacy cards used host-native Windows separators. Evidence remains strict.
    return relative.replace("\\", "/") if isinstance(relative, str) else relative


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        match = re.match(r"^([A-Za-z ]+):\s*(.+)$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2).strip()
    return metadata


def headings(text: str) -> set[str]:
    return {match.group(1).strip() for match in re.finditer(r"^##\s+(.+)$", text, flags=re.MULTILINE)}


def related_files(text: str) -> list[str]:
    match = re.search(r"^## Related files\s*$", text, flags=re.MULTILINE)
    if not match:
        return []
    start = match.end()
    next_match = re.search(r"^## .+$", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    section = text[start:end]
    paths = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip().strip("`")
        if value and not value.startswith("TODO"):
            paths.append(value)
    return paths


def validate_date(value: str, label: str, problems: list[str]) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        problems.append(f"{label} must be YYYY-MM-DD: {value}")


def validate_card(entry: dict[str, Any], problems: list[str], root: Path = ROOT) -> None:
    text = read_source(root, legacy_relative(entry["path"]))
    metadata = parse_metadata(text)
    missing_metadata = sorted(REQUIRED_CARD_FIELDS - set(metadata))
    for field in missing_metadata:
        problems.append(f"{entry['path']}: missing metadata field {field}")

    card_headings = headings(text)
    for heading in sorted(REQUIRED_HEADINGS - card_headings):
        problems.append(f"{entry['path']}: missing heading ## {heading}")
    if "Content" not in card_headings and "Procedure" not in card_headings:
        problems.append(f"{entry['path']}: missing ## Content or ## Procedure")

    if metadata.get("Type") and metadata["Type"] != entry["type"]:
        problems.append(f"{entry['path']}: Type does not match index entry")
    if metadata.get("Scope") and metadata["Scope"] != entry["scope"]:
        problems.append(f"{entry['path']}: Scope does not match index entry")
    if metadata.get("Confidence") and metadata["Confidence"] != entry["confidence"]:
        problems.append(f"{entry['path']}: Confidence does not match index entry")
    if metadata.get("Last verified"):
        validate_date(metadata["Last verified"], f"{entry['path']} Last verified", problems)
        if "evidence" in entry and metadata["Last verified"] != entry["last_verified"]:
            problems.append(f"{entry['path']}: Last verified does not match index entry")
    if metadata.get("Source task") and not as_path(metadata["Source task"], root).is_file():
        problems.append(f"{entry['path']}: Source task does not exist: {metadata['Source task']}")
    if "evidence" in entry and legacy_relative(metadata.get("Source task")) != legacy_relative(entry["source_task"]):
        problems.append(f"{entry['path']}: Source task does not match index entry")
    if "verification_record" in entry:
        read_source(root, legacy_relative(entry["verification_record"]))
        if metadata.get("Verification record") != entry["verification_record"]:
            problems.append(f"{entry['path']}: Verification record does not match index entry")

    for related in related_files(text):
        if not as_path(related, root).is_file():
            problems.append(f"{entry['path']}: related file does not exist: {related}")


def validate(root: Path = ROOT, require_evidence: list[str] | None = None) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    statuses: list[str] = []
    try:
        data = load_index(root)
    except (EvidenceError, OSError, ValueError) as exc:
        return [f"Cannot read memory index: {exc}"], statuses
    if data.get("version") != 1:
        problems.append("index version must be 1")
    memories = data.get("memories")
    if not isinstance(memories, list):
        problems.append("index memories must be a list")
        memories = []

    seen_ids: set[str] = set()
    for entry in memories:
        if not isinstance(entry, dict):
            problems.append("memory entry must be an object")
            continue
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        entry_id = entry.get("id", "<missing id>")
        for field in missing:
            problems.append(f"{entry_id}: missing index field {field}")
        if missing:
            continue

        string_fields = REQUIRED_ENTRY_FIELDS - {"keywords"}
        if any(not isinstance(entry[key], str) or not entry[key] for key in string_fields):
            problems.append(f"{entry_id}: entry metadata must contain non-empty strings")
            continue
        if entry["id"] in seen_ids:
            problems.append(f"{entry['id']}: duplicate memory id")
        seen_ids.add(entry["id"])
        if entry["type"] not in VALID_TYPES:
            problems.append(f"{entry['id']}: invalid type {entry['type']}")
        if entry["confidence"] not in VALID_CONFIDENCE:
            problems.append(f"{entry['id']}: invalid confidence {entry['confidence']}")
        if not isinstance(entry["keywords"], list) or not all(isinstance(item, str) for item in entry["keywords"]):
            problems.append(f"{entry['id']}: keywords must be a list of strings")
        validate_date(entry["last_verified"], f"{entry['id']} last_verified", problems)
        try:
            if not as_path(entry["source_task"], root).is_file():
                problems.append(f"{entry['id']}: source_task does not exist: {entry['source_task']}")
            validate_card(entry, problems, root)
        except (EvidenceError, OSError) as exc:
            problems.append(f"{entry['id']}: {exc}")
        required = require_evidence is not None and (not require_evidence or entry["id"] in require_evidence)
        evidence = inspect_evidence(root, entry, required=required)
        statuses.append(f"{entry['id']}: {evidence.status}")
        if evidence.status not in {"unchanged", "untracked"}:
            problems.extend(f"{entry['id']}: {evidence.status}: {detail}" for detail in evidence.details)

    for unknown in sorted(set(require_evidence or []) - seen_ids):
        problems.append(f"Unknown memory id requiring evidence: {unknown}")
    return problems, statuses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate memory links and optional source evidence.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-evidence", nargs="*", metavar="ID", help="Require evidence for listed IDs, or all entries when no IDs follow.")
    args = parser.parse_args(argv)
    problems, statuses = validate(args.root, args.require_evidence)
    for status in statuses:
        print(status)

    if problems:
        for problem in problems:
            print(problem)
        return 1

    print(f"Memory index and {len(statuses)} promoted memory cards look valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
